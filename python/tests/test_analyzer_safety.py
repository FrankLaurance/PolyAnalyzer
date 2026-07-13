import os
import json
import sys
import tempfile
import types
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

import numpy as np


PYTHON_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PYTHON_DIR.parent
sys.path.insert(0, str(PYTHON_DIR))

# Keep the legacy import-time logger away from the repository while RED tests run.
_IMPORT_TMP = tempfile.TemporaryDirectory()
_ORIGINAL_CWD = os.getcwd()
os.chdir(_IMPORT_TMP.name)
os.environ["POLYANALYZER_DISABLE_FILE_LOG"] = "1"
os.environ["MPLCONFIGDIR"] = str(Path(_IMPORT_TMP.name, "matplotlib"))
os.environ["XDG_CACHE_HOME"] = str(Path(_IMPORT_TMP.name, "xdg"))
try:
    from analyzer import base, dsc, gpc, ir, mw
    import api
finally:
    os.environ.pop("POLYANALYZER_DISABLE_FILE_LOG", None)
    os.chdir(_ORIGINAL_CWD)


class InstallAndNameSafetyTests(unittest.TestCase):
    def test_app_versions_are_consistent(self):
        package_version = json.loads(
            (PROJECT_ROOT / "package.json").read_text(encoding="utf-8")
        )["version"]
        tauri_version = json.loads(
            (PROJECT_ROOT / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
        )["version"]
        self.assertEqual(package_version, base.APP_VERSION)
        self.assertEqual(package_version, tauri_version)

    def test_development_install_dir_is_project_root(self):
        self.assertEqual(str(PROJECT_ROOT), base.get_install_dir())

    def test_data_dir_override_applies_in_development(self):
        with tempfile.TemporaryDirectory() as temp_dir, \
                patch.dict(os.environ, {"POLYANALYZER_DATA_DIR": temp_dir}):
            self.assertEqual(str(Path(temp_dir).resolve()), base.get_install_dir())

    def test_analysis_profiles_are_isolated_and_seed_legacy_defaults(self):
        with tempfile.TemporaryDirectory() as temp_dir, \
                patch.dict(os.environ, {"POLYANALYZER_DATA_DIR": temp_dir}):
            setting_dir = Path(temp_dir, "setting")
            setting_dir.mkdir()
            (setting_dir / "defaultSetting.ini").write_text("{}", encoding="utf-8")

            mw_dir = Path(base.get_profile_dir("mw"))
            ir_dir = Path(base.get_profile_dir("ir"))

            self.assertNotEqual(mw_dir, ir_dir)
            self.assertTrue((mw_dir / "defaultSetting.ini").is_file())
            self.assertFalse((ir_dir / "defaultSetting.ini").exists())

    def test_frozen_install_without_project_uses_user_data_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            executable = root / "read-only-app" / "poly"
            executable.parent.mkdir()
            user_data = root / "user-data"
            with patch.object(base.sys, "frozen", True, create=True), \
                    patch.object(base.sys, "executable", str(executable)), \
                    patch.dict(os.environ, {"POLYANALYZER_DATA_DIR": str(user_data)}):
                install_dir = base.get_install_dir()

            self.assertEqual(str(user_data.resolve()), install_dir)
            self.assertTrue(user_data.is_dir())
            self.assertNotEqual(str(executable.parent), install_dir)

    def test_logger_uses_install_data_not_cwd_or_executable_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cwd = root / "cwd"
            cwd.mkdir()
            executable = root / "app" / "poly"
            executable.parent.mkdir()
            user_data = root / "user-data"
            original_cwd = os.getcwd()
            os.chdir(cwd)
            try:
                with patch.object(base.sys, "frozen", True, create=True), \
                        patch.object(base.sys, "executable", str(executable)), \
                        patch.dict(os.environ, {"POLYANALYZER_DATA_DIR": str(user_data)}):
                    logger = base.Logger(name=f"test-{uuid.uuid4()}")
            finally:
                os.chdir(original_cwd)

            paths = [Path(handler.baseFilename) for handler in logger.logger.handlers]
            self.assertEqual(1, len(paths))
            self.assertEqual((user_data / "logs").resolve(), paths[0].parent.resolve())
            self.assertNotEqual(cwd.resolve(), paths[0].parent.resolve())
            self.assertNotEqual(executable.parent.resolve(), paths[0].parent.resolve())
            for handler in list(logger.logger.handlers):
                handler.close()
                logger.logger.removeHandler(handler)

    def test_settings_name_must_be_a_basename(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = base.SettingsManager(temp_dir, "default.ini", {})
            for unsafe in ("../escape.ini", "nested/escape.ini", "nested\\escape.ini"):
                with self.subTest(unsafe=unsafe):
                    with self.assertRaises(ValueError):
                        manager.get_setting_path(unsafe)

    def test_settings_list_excludes_non_profile_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = base.SettingsManager(temp_dir, "default.ini", {})
            for name in ("default.ini", "publication.json", "language.json", ".DS_Store", "notes.txt"):
                Path(temp_dir, name).write_text("{}", encoding="utf-8")

            self.assertEqual(["default.ini", "publication.json"], manager.list_settings())

    def test_gpc_output_name_must_be_a_basename(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                gpc.GPCAnalyzer(temp_dir, "../escape")

    def test_gpc_overwrite_check_includes_xlsx(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "data"
            data_dir.mkdir()
            output_dir = root / "GPC_output"
            output_dir.mkdir()
            (output_dir / "report.xlsx").write_text("existing", encoding="utf-8")

            analyzer = gpc.GPCAnalyzer(str(data_dir), "report")

            self.assertTrue(analyzer.check_dir())

    def test_gpc_failure_preserves_previous_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "data"
            data_dir.mkdir()
            old = root / "GPC_output" / "old.txt"
            old.parent.mkdir()
            old.write_text("keep", encoding="utf-8")
            analyzer = gpc.GPCAnalyzer(str(data_dir), "report")
            analyzer.selected_file = ["missing.rst"]

            self.assertFalse(analyzer.run())
            self.assertEqual("keep", old.read_text(encoding="utf-8"))

    def test_excel_sheet_names_are_valid_bounded_and_unique(self):
        first = gpc.make_unique_sheet_name("sample[]:*?/\\" + "x" * 40, [])
        second = gpc.make_unique_sheet_name("sample[]:*?/\\" + "x" * 40, [first])

        self.assertLessEqual(len(first), 31)
        self.assertLessEqual(len(second), 31)
        self.assertFalse(any(char in first for char in "[]:*?/\\"))
        self.assertNotEqual(first.casefold(), second.casefold())


class MolecularWeightFailureTests(unittest.TestCase):
    def test_all_failed_mw_inputs_return_false_and_api_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "data"
            data_dir.mkdir()
            old = root / "Mw_output" / "old.txt"
            old.parent.mkdir()
            old.write_text("keep", encoding="utf-8")
            analyzer = mw.MolecularWeightAnalyzer(str(data_dir), draw_table=False)
            analyzer.selected_file = ["missing.rst"]
            with patch.object(mw, "configure_plotting", return_value=object()):
                self.assertFalse(analyzer.run())
            self.assertEqual("keep", old.read_text(encoding="utf-8"))

            with patch.object(mw, "configure_plotting", return_value=object()):
                response = api._handle_request({
                    "jsonrpc": "2.0",
                    "method": "mw.analyze",
                    "params": {
                        "datadir": str(data_dir),
                        "selected_files": ["missing.rst"],
                        "draw_table": False,
                    },
                    "id": 11,
                })
            self.assertIn("error", response)


class IrRegressionTests(unittest.TestCase):
    def test_ir_defaults_to_red_peak_normalized_overlay(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ir, "get_install_dir", return_value=temp_dir):
                analyzer = ir.IRAnalyzer(temp_dir)

        self.assertEqual("#D62728", analyzer.curve_color)
        self.assertTrue(analyzer.draw_overlay)
        self.assertTrue(analyzer.normalize_overlay)
        self.assertEqual(1450.0, analyzer.normalization_peak)

    def test_transmittance_uses_unclamped_absorbance(self):
        absorbance = np.array([1.99, 2.0, 3.0])
        expected = 10.0 ** (2.0 - absorbance)
        np.testing.assert_allclose(expected, ir.IRAnalyzer.absorbance_to_transmittance(absorbance))

    def test_peak_normalization_scales_selected_absorbance_peak(self):
        wavenumber = np.array([1600.0, 1450.0, 1300.0])
        transmittance = np.array([100.0, 50.0, 80.0])

        normalized = ir.IRAnalyzer.normalize_to_peak(
            wavenumber,
            transmittance,
            center=1450.0,
            window=20.0,
        )

        normalized_absorbance = 2.0 - np.log10(normalized)
        self.assertAlmostEqual(0.6, normalized_absorbance[1], places=6)

    def test_ir_can_skip_overlay_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "data"
            data_dir.mkdir()
            (data_dir / "sample.dpt").write_text(
                "4000 0.1\n3900 0.2\n",
                encoding="utf-8",
            )
            with patch.object(ir, "get_install_dir", return_value=temp_dir):
                analyzer = ir.IRAnalyzer(
                    str(data_dir),
                    selected_files=["sample.dpt"],
                    draw_overlay=False,
                )

            def fake_individual(_plt, _wn, _transmittance, _title, output_path):
                Path(output_path).write_text("image", encoding="utf-8")

            with patch.object(ir, "configure_plotting", return_value=object()), \
                    patch.object(analyzer, "plot_spectrum", side_effect=fake_individual), \
                    patch.object(analyzer, "plot_overlay") as plot_overlay:
                self.assertTrue(analyzer.run())

            plot_overlay.assert_not_called()
            self.assertEqual(
                [str(Path("individual", "sample.png")), "manifest.json"],
                [str(Path(path).relative_to(analyzer.output_dir)) for path in analyzer.generated_files],
            )

    def test_dpt_rejects_non_finite_or_fewer_than_two_points(self):
        cases = {
            "nan.dpt": "4000 NaN\n3900 0.5\n",
            "inf.dpt": "4000 Inf\n3900 0.5\n",
            "short.dpt": "4000 0.5\n",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            for filename, content in cases.items():
                path = Path(temp_dir, filename)
                path.write_text(content, encoding="utf-8")
                with self.subTest(filename=filename):
                    with self.assertRaises(ValueError):
                        ir.IRAnalyzer.parse_dpt(str(path))

    def test_ir_file_list_returns_regular_files_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "sample.dpt").write_text("4000 0.1\n3900 0.2\n", encoding="utf-8")
            Path(temp_dir, "folder.dpt").mkdir()
            with patch.object(ir, "get_install_dir", return_value=temp_dir):
                analyzer = ir.IRAnalyzer(temp_dir)
            self.assertEqual(["sample.dpt"], analyzer.read_file_list())

    def test_ir_failure_preserves_previous_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "data"
            data_dir.mkdir()
            (data_dir / "sample.dpt").write_text("4000 0.1\n3900 0.2\n", encoding="utf-8")
            old_output = root / "IR_output"
            old_output.mkdir()
            sentinel = old_output / "old.txt"
            sentinel.write_text("keep", encoding="utf-8")

            with patch.object(ir, "get_install_dir", return_value=temp_dir):
                analyzer = ir.IRAnalyzer(str(data_dir), selected_files=["sample.dpt"])

            def fake_individual(_plt, _wn, _transmittance, _title, output_path):
                Path(output_path).write_text("new", encoding="utf-8")

            with patch.object(ir, "configure_plotting", return_value=object()), \
                    patch.object(analyzer, "plot_spectrum", side_effect=fake_individual), \
                    patch.object(analyzer, "plot_overlay", side_effect=RuntimeError("plot failed")):
                with self.assertRaises(RuntimeError):
                    analyzer.run()

            self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))


class DscRegressionTests(unittest.TestCase):
    def _make_valid_analyzer(self, root, progress):
        data_dir = root / "data"
        data_dir.mkdir()
        (data_dir / "sample.txt").write_text("placeholder", encoding="utf-8")
        analyzer = dsc.DSCAnalyzer(
            str(data_dir),
            save_seg_mode=True,
            draw_seg_mode=False,
            draw_cycle=True,
            display_pic=True,
            progress_callback=lambda value, _message: progress.append(value),
        )
        analyzer.selected_file = ["sample.txt"]

        def fake_read_file(self, name, reset_peak_data=True):
            self.reset()
            self.filename = name
            return True

        def fake_preprocess(self):
            self.data = np.array([[0.0, 10.0, 1.0], [1.0, 11.0, 2.0]], dtype=float)
            self.region = [[0.0, 1.0], [1.0, 2.0]]
            self.data_seg = [self.data, self.data]

        def fake_save(self):
            for cycle in ("Cycle1", "Cycle2"):
                path = Path(self.cycle_dir, cycle)
                path.mkdir(parents=True, exist_ok=True)
                np.savetxt(path / "sample.csv", np.array([[10.0, 1.0], [11.0, 2.0]]), delimiter=",")

        analyzer.read_file = types.MethodType(fake_read_file, analyzer)
        analyzer.preprocess = types.MethodType(fake_preprocess, analyzer)
        analyzer.save_data_seg = types.MethodType(fake_save, analyzer)
        return analyzer

    def test_all_failed_dsc_inputs_return_false_without_clearing_old_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "data"
            data_dir.mkdir()
            cycle_old = root / "DSC_Cycle" / "Cycle1" / "old.csv"
            cycle_old.parent.mkdir(parents=True)
            cycle_old.write_text("old", encoding="utf-8")
            pic_old = root / "DSC_Pic" / "sample" / "old.png"
            pic_old.parent.mkdir(parents=True)
            pic_old.write_text("old", encoding="utf-8")

            analyzer = dsc.DSCAnalyzer(
                str(data_dir),
                save_seg_mode=False,
                draw_seg_mode=False,
                draw_cycle=False,
                display_pic=False,
            )
            analyzer.selected_file = ["missing.txt"]

            self.assertFalse(analyzer.run())
            self.assertEqual("old", cycle_old.read_text(encoding="utf-8"))
            self.assertEqual("old", pic_old.read_text(encoding="utf-8"))

    def test_dsc_progress_is_monotonic_and_all_figures_are_closed(self):
        dsc.plt.close("all")
        progress = []
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = self._make_valid_analyzer(Path(temp_dir), progress)
            self.assertTrue(analyzer.run())

        self.assertEqual(sorted(progress), progress)
        self.assertEqual([], dsc.plt.get_fignums())

    def test_dsc_processing_failure_preserves_previous_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            progress = []
            analyzer = self._make_valid_analyzer(root, progress)
            old = root / "DSC_Cycle" / "Cycle1" / "old.csv"
            old.parent.mkdir(parents=True, exist_ok=True)
            old.write_text("keep", encoding="utf-8")
            analyzer.draw_seg_mode = True
            analyzer.draw_img = types.MethodType(
                lambda self: (_ for _ in ()).throw(RuntimeError("draw failed")),
                analyzer,
            )

            self.assertFalse(analyzer.run())
            self.assertEqual("keep", old.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
