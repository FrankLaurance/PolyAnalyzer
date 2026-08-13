"""
Tests for analyzer/excel_reader.py — GPC Excel export format parsing.

Covers auto-detection of per-sample LogM/MMD/Cumulative column groups
(arbitrary column counts) and the conventional Results summary sheet.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

PYTHON_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PYTHON_DIR))

# Keep the legacy import-time logger away from the repository while tests run.
_IMPORT_TMP = tempfile.TemporaryDirectory()
_ORIGINAL_CWD = os.getcwd()
os.chdir(_IMPORT_TMP.name)
os.environ["POLYANALYZER_DISABLE_FILE_LOG"] = "1"
os.environ["POLYANALYZER_DATA_DIR"] = str(Path(_IMPORT_TMP.name, "data"))
try:
    from analyzer.excel_reader import parse_gpc_excel
    from analyzer import gpc, mw
    import api
    import cli
finally:
    os.environ.pop("POLYANALYZER_DISABLE_FILE_LOG", None)
    os.environ.pop("POLYANALYZER_DATA_DIR", None)
    os.chdir(_ORIGINAL_CWD)


_LOG_M = np.linspace(6.0, 7.0, 6)  # 6 points, ascending


def _make_workbook(
    path: Path,
    *,
    with_cumulative: bool = True,
    with_mmd: bool = True,
    with_results: bool = True,
    extra_sample: bool = False,
) -> None:
    """Build a synthetic GPC export workbook mimicking the instrument format."""
    samples = ["26-2613 (GPP-262-1#)", "26-2612 (GPP-262-2#)"]
    if extra_sample:
        samples.append("26-2611 (GPP-262-3#)")

    data_header: list = []
    data_rows: list[list] = []
    # LogM is monotonically decreasing in real exports.
    logm = _LOG_M[::-1]
    for idx, name in enumerate(samples):
        mmd = np.array([0.0, 0.3, 0.4, 0.15, 0.03, 0.02]) * (1.0 + 0.1 * idx)
        cumulative = np.cumsum(mmd) / np.sum(mmd)
        if with_mmd:
            data_header += ["LogM", f"{name} MMD"]
            data_rows.append(list(logm))
            data_rows.append(list(mmd))
        if with_cumulative:
            data_header += ["LogM", f"{name} Cumulative"]
            data_rows.append(list(logm))
            data_rows.append(list(cumulative))

    data_df = pd.DataFrame(np.column_stack(data_rows))
    data_df.columns = data_header

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        data_df.to_excel(writer, sheet_name="Data", index=False, header=True)
        if with_results:
            results = pd.DataFrame(
                [
                    ["Conventional", "", "", "", "", "", "", "", ""],
                    ["", "Mw (g/mol)", "Mn (g/mol)", "Mw / Mn",
                     "Mz (g/mol)", "Mz1 (g/mol)", "Mz / Mw",
                     "Mv (g/mol)", "Mp (g/mol)"],
                    [samples[0], "520,600", "28,600", "18.19",
                     "2,234,600", "5,041,600", "4.29", "404,300", "181,400"],
                    [samples[1], "503,600", "22,700", "22.20",
                     "2,773,200", "6,599,500", "5.51", "374,100", "143,900"],
                    [samples[2] if extra_sample else "", "919,000", "45,500",
                     "20.19", "3,816,800", "8,003,500", "4.15",
                     "715,900", "503,900"],
                ]
            )
            results.to_excel(writer, sheet_name="Results", index=False, header=False)


class GpcExcelParserTests(unittest.TestCase):
    """Behavior of parse_gpc_excel on instrument-style workbooks."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_parses_multi_sample_mmd_and_cumulative_columns(self) -> None:
        path = self.tmp_path / "gpc.xlsx"
        _make_workbook(path, extra_sample=True)

        samples = parse_gpc_excel(str(path))

        self.assertEqual(
            list(samples),
            ["26-2613 (GPP-262-1#)", "26-2612 (GPP-262-2#)", "26-2611 (GPP-262-3#)"],
        )
        first = samples["26-2613 (GPP-262-1#)"]
        np.testing.assert_allclose(first.logm, _LOG_M)
        self.assertTrue(np.all(np.diff(first.logm) > 0), "logm must be ascending")
        # Instrument exports accumulate cumulative weight fraction along
        # descending logM rows; after ascending re-sorting the series
        # starts at 1.0 and decreases monotonically.
        self.assertAlmostEqual(float(first.cumulative[0]), 1.0, places=6)
        self.assertTrue(np.all(np.diff(first.cumulative) <= 0))
        self.assertEqual(first.results["Mw"], 520600.0)
        self.assertEqual(first.results["Mn"], 28600.0)
        self.assertEqual(first.results["Mz"], 2234600.0)
        self.assertEqual(first.results["Mz+1"], 5041600.0)
        self.assertEqual(first.results["Mv"], 404300.0)
        self.assertEqual(first.results["Mp"], 181400.0)
        self.assertAlmostEqual(first.results["PD"], 18.19)
        # The instrument rounds the printed ratio; allow one decimal place.
        self.assertAlmostEqual(
            float(first.results["PD"]), float(first.results["Mw"] / first.results["Mn"]),
            places=1,
        )

    def test_derives_missing_cumulative_from_mmd(self) -> None:
        path = self.tmp_path / "gpc.xlsx"
        _make_workbook(path, with_cumulative=False)

        samples = parse_gpc_excel(str(path))
        first = samples["26-2613 (GPP-262-1#)"]

        self.assertAlmostEqual(float(first.cumulative[-1]), 1.0, places=4)

    def test_derives_missing_mmd_from_cumulative(self) -> None:
        path = self.tmp_path / "gpc.xlsx"
        _make_workbook(path, with_mmd=False)

        samples = parse_gpc_excel(str(path))
        first = samples["26-2613 (GPP-262-1#)"]

        # Reintegrating the derived dw/dlogM must recover the cumulative mass.
        integral = float(np.trapezoid(first.mmd, first.logm))
        self.assertAlmostEqual(integral, 1.0, places=4)

    def test_missing_results_sheet_yields_empty_results(self) -> None:
        path = self.tmp_path / "gpc.xlsx"
        _make_workbook(path, with_results=False)

        samples = parse_gpc_excel(str(path))
        self.assertEqual(samples["26-2613 (GPP-262-1#)"].results, {})

    def test_rejects_workbook_without_recognizable_data(self) -> None:
        path = self.tmp_path / "gpc.xlsx"
        pd.DataFrame({"A": [1, 2], "B": [3, 4]}).to_excel(path, index=False)

        with self.assertRaises(ValueError):
            parse_gpc_excel(str(path))


class GpcExcelAnalyzerTests(unittest.TestCase):
    """End-to-end analyzer behavior on Excel input files."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)
        self.datapath = self.tmp_path / "datapath"
        self.datapath.mkdir()
        _make_workbook(self.datapath / "gpc-export.xlsx")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_gpc_analyzer_outputs_overlay_csv_and_per_sample_sheets(self) -> None:
        analyzer = gpc.GPCAnalyzer(
            str(self.datapath), "excel-out",
            save_file=True, save_picture=True,
        )
        analyzer.selected_file = ["gpc-export.xlsx"]

        self.assertTrue(analyzer.run())

        outdir = self.tmp_path / "GPC_output"
        self.assertTrue((outdir / "excel-out.png").is_file())
        self.assertGreater((outdir / "excel-out.png").stat().st_size, 0)

        csv_text = (outdir / "excel-out.csv").read_text(encoding="utf-8")
        self.assertIn("26-2613 (GPP-262-1#)", csv_text)
        self.assertIn("520600", csv_text)
        self.assertIn("26-2612 (GPP-262-2#)", csv_text)
        self.assertIn("503600", csv_text)

        with pd.ExcelFile(outdir / "excel-out.xlsx") as xlsx:
            self.assertIn("26-2613 (GPP-262-1#)", xlsx.sheet_names)
            self.assertIn("26-2612 (GPP-262-2#)", xlsx.sheet_names)

    def test_mw_analyzer_emits_one_figure_per_sample(self) -> None:
        analyzer = mw.MolecularWeightAnalyzer(
            str(self.datapath), draw_table=False,
        )
        analyzer.selected_file = ["gpc-export.xlsx"]

        self.assertTrue(analyzer.run())

        outdir = self.tmp_path / "Mw_output"
        for name in ("26-2613 (GPP-262-1#)", "26-2612 (GPP-262-2#)"):
            png = outdir / f"{name}.png"
            self.assertTrue(png.is_file(), f"missing figure for {name}")
            self.assertGreater(png.stat().st_size, 0)

    def test_gpc_summary_csv_accumulates_all_input_files(self) -> None:
        """多文件分析时汇总 CSV 必须覆盖每个输入文件，而不是只留最后一个。"""
        second = self.datapath / "gpc-export-2.xlsx"
        _make_workbook(second, extra_sample=True)

        analyzer = gpc.GPCAnalyzer(
            str(self.datapath), "multi-out",
            save_file=True, save_picture=False,
            save_figure_file_gpc=False,
        )
        analyzer.selected_file = ["gpc-export.xlsx", "gpc-export-2.xlsx"]

        self.assertTrue(analyzer.run())

        csv_text = (self.tmp_path / "GPC_output" / "multi-out.csv").read_text(encoding="utf-8")
        data_rows = csv_text.strip().splitlines()[1:]
        self.assertEqual(5, len(data_rows), f"expected 5 sample rows, got:\n{csv_text}")
        self.assertIn("26-2611 (GPP-262-3#)", csv_text)
        self.assertIn("520600", csv_text)   # 第一个文件的样品仍在
        self.assertIn("919000", csv_text)   # 第二个文件的第三个样品仍在


class GpcExcelListingTests(unittest.TestCase):
    """Excel files must be listed and accepted by the GUI sidecar and CLI."""

    def test_gpc_list_files_includes_excel_workbooks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            for name in ("a.rst", "b.xls", "c.xlsx", "d.XLS", "e.txt", "f.rst.bak"):
                (data_dir / name).write_bytes(b"x")

            files = api._gpc_list_files({"datadir": str(data_dir)})["files"]

        self.assertEqual(files, ["a.rst", "b.xls", "c.xlsx", "d.XLS"])

    def test_mw_list_files_includes_excel_workbooks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            (data_dir / "b.xlsx").write_bytes(b"x")

            files = api._mw_list_files({"datadir": str(data_dir)})["files"]

        self.assertEqual(files, ["b.xlsx"])

    def test_api_accepts_excel_selected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            (data_dir / "b.xls").write_bytes(b"x")

            files = api._validate_selected_files(
                str(data_dir), ["b.xls"], (".rst", ".xls", ".xlsx"), required=True,
            )

        self.assertEqual(files, ["b.xls"])

    def test_cli_accepts_excel_selected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            (data_dir / "b.xlsx").write_bytes(b"x")

            files = cli._validate_selected_files(
                str(data_dir), ["b.xlsx"], ("*.rst", "*.xls", "*.xlsx"),
            )

        self.assertEqual(files, ["b.xlsx"])


if __name__ == "__main__":
    unittest.main()
