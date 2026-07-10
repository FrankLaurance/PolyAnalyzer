import argparse
import contextlib
import inspect
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PYTHON_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PYTHON_DIR))

_IMPORT_TMP = tempfile.TemporaryDirectory()
os.environ["POLYANALYZER_DISABLE_FILE_LOG"] = "1"
os.environ["MPLCONFIGDIR"] = str(Path(_IMPORT_TMP.name, "matplotlib"))
try:
    import api
    import build_sidecar
    import cli
finally:
    os.environ.pop("POLYANALYZER_DISABLE_FILE_LOG", None)


class ApiInputValidationTests(unittest.TestCase):
    def test_selected_filenames_reject_path_components_for_every_analyzer(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            requests = {
                "gpc.analyze": {
                    "datadir": temp_dir,
                    "output_filename": "result",
                    "selected_files": ["../outside.rst"],
                    "confirm_overwrite": True,
                },
                "mw.analyze": {
                    "datadir": temp_dir,
                    "selected_files": ["../outside.rst"],
                },
                "dsc.analyze": {
                    "datadir": temp_dir,
                    "selected_files": ["../outside.txt"],
                },
                "ir.analyze": {
                    "datadir": temp_dir,
                    "selected_files": ["../outside.dpt"],
                },
            }

            for method, params in requests.items():
                with self.subTest(method=method):
                    response = api._handle_request({
                        "jsonrpc": "2.0",
                        "method": method,
                        "params": params,
                        "id": method,
                    })
                    self.assertEqual(api.INVALID_PARAMS, response["error"]["code"])

    def test_gpc_output_and_setting_names_map_to_invalid_params(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            gpc_response = api._handle_request({
                "jsonrpc": "2.0",
                "method": "gpc.check_output",
                "params": {"datadir": temp_dir, "output_filename": "../escape"},
                "id": 1,
            })
            settings_response = api._handle_request({
                "jsonrpc": "2.0",
                "method": "settings.load",
                "params": {"name": "../escape.ini"},
                "id": 2,
            })

        self.assertEqual(api.INVALID_PARAMS, gpc_response["error"]["code"])
        self.assertEqual(api.INVALID_PARAMS, settings_response["error"]["code"])

    def test_ir_overlay_options_validate_types_and_peak_range(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "sample.dpt").write_text(
                "4000 0.1\n3900 0.2\n",
                encoding="utf-8",
            )
            invalid_values = (
                {"draw_overlay": "yes"},
                {"normalize_overlay": 1},
                {"normalization_peak": 399},
                {"normalization_peak": 4001},
            )
            for index, invalid in enumerate(invalid_values):
                with self.subTest(invalid=invalid):
                    response = api._handle_request({
                        "jsonrpc": "2.0",
                        "method": "ir.analyze",
                        "params": {
                            "datadir": temp_dir,
                            "selected_files": ["sample.dpt"],
                            **invalid,
                        },
                        "id": index,
                    })
                    self.assertEqual(api.INVALID_PARAMS, response["error"]["code"])


class CliSafetyTests(unittest.TestCase):
    def test_cli_file_listing_returns_regular_files_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "sample.rst").write_text("data", encoding="utf-8")
            Path(temp_dir, "folder.rst").mkdir()
            self.assertEqual(["sample.rst"], cli._list_files(temp_dir, "*.rst"))

    def test_cli_selected_filename_rejects_traversal_even_when_target_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "data"
            data_dir.mkdir()
            (root / "outside.rst").write_text("data", encoding="utf-8")
            with self.assertRaises(cli.CliError) as caught:
                cli._validate_selected_files(str(data_dir), ["../outside.rst"], "*.rst")
            self.assertEqual(cli.EXIT_ARGUMENT_ERROR, caught.exception.exit_code)

    def test_unhandled_exception_with_json_flag_returns_stable_json(self):
        args = argparse.Namespace(
            json=True,
            func=lambda _args: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        class FakeParser:
            def parse_args(self, _argv):
                return args

        stdout = io.StringIO()
        with patch.object(cli, "build_parser", return_value=FakeParser()), \
                contextlib.redirect_stdout(stdout):
            exit_code = cli.main([])

        self.assertEqual(cli.EXIT_ANALYSIS_FAILED, exit_code)
        self.assertEqual(
            {"success": False, "error": "Internal error"},
            json.loads(stdout.getvalue()),
        )


class PackagingTests(unittest.TestCase):
    def test_hidden_imports_are_split_and_cli_excludes_ir_and_scipy(self):
        sidecar = set(build_sidecar.SIDECAR_HIDDEN_IMPORTS)
        cli_imports = set(build_sidecar.CLI_HIDDEN_IMPORTS)

        self.assertIn("analyzer.ir", sidecar)
        self.assertNotIn("analyzer.ir", cli_imports)
        self.assertNotIn("scipy", sidecar)
        self.assertNotIn("scipy", cli_imports)
        self.assertTrue({"analyzer.gpc", "analyzer.mw", "analyzer.dsc"} <= cli_imports)

    def test_build_executable_requires_explicit_hidden_imports(self):
        parameters = inspect.signature(build_sidecar.build_executable).parameters
        self.assertIn("hidden_imports", parameters)

    def test_python_requirements_do_not_include_unused_scipy(self):
        requirements = (PYTHON_DIR / "requirements.txt").read_text(encoding="utf-8")
        self.assertNotIn("scipy", requirements.casefold())


if __name__ == "__main__":
    unittest.main()
