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
                "method": "gpc.analyze",
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
    def test_cli_exposes_ir_analysis_and_profiles(self):
        parser = cli.build_parser()
        ir_args = parser.parse_args([
            "ir",
            "--datadir",
            "/tmp",
            "--no-overlay",
            "--normalization-peak",
            "1450",
        ])
        profile_args = parser.parse_args(["settings", "list", "--type", "ir"])

        self.assertIs(ir_args.func, cli._run_ir)
        self.assertFalse(ir_args.draw_overlay)
        self.assertEqual(1450.0, ir_args.normalization_peak)
        self.assertEqual("ir", profile_args.type)

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

    def test_cli_stream_configuration_emits_utf8_json_and_progress(self):
        stdin_bytes = io.BytesIO()
        stdout_bytes = io.BytesIO()
        stderr_bytes = io.BytesIO()
        stdin = io.TextIOWrapper(stdin_bytes, encoding="gbk")
        stdout = io.TextIOWrapper(stdout_bytes, encoding="gbk", newline="\r\n")
        stderr = io.TextIOWrapper(stderr_bytes, encoding="gbk", newline="\r\n")
        args = argparse.Namespace(json=True, quiet=False)

        with (
            patch.object(cli.sys, "stdin", stdin),
            patch.object(cli.sys, "stdout", stdout),
            patch.object(cli.sys, "stderr", stderr),
        ):
            cli._configure_standard_streams()
            self.assertEqual(
                ("utf-8", "strict"),
                (cli.sys.stdin.encoding, cli.sys.stdin.errors),
            )
            self.assertEqual(
                ("utf-8", "strict"),
                (cli.sys.stdout.encoding, cli.sys.stdout.errors),
            )
            self.assertEqual(
                ("utf-8", "backslashreplace"),
                (cli.sys.stderr.encoding, cli.sys.stderr.errors),
            )
            progress = cli._progress_callback(args)
            self.assertIsNotNone(progress)
            progress(0.5, "中文进度")
            cli._emit_result(args, {"success": True, "files": ["样品.rst"]})
            cli.sys.stdout.flush()
            cli.sys.stderr.flush()

        self.assertEqual(
            {"success": True, "files": ["样品.rst"]},
            json.loads(stdout_bytes.getvalue().decode("utf-8")),
        )
        self.assertEqual(
            ["[ 50.00%] 中文进度"],
            stderr_bytes.getvalue().decode("utf-8").splitlines(),
        )

    def test_programmatic_main_does_not_reconfigure_consumed_stdin(self):
        stdin = io.TextIOWrapper(io.BytesIO(b"already read\n"), encoding="utf-8")
        stdin.readline()
        args = argparse.Namespace(func=lambda _args: cli.EXIT_OK)

        class FakeParser:
            def parse_args(self, _argv):
                return args

        with (
            patch.object(cli, "build_parser", return_value=FakeParser()),
            patch.object(cli.sys, "stdin", stdin),
        ):
            exit_code = cli.main([])

        self.assertEqual(cli.EXIT_OK, exit_code)


class PackagingTests(unittest.TestCase):
    def test_hidden_imports_include_all_analyzers_and_exclude_scipy(self):
        sidecar = set(build_sidecar.SIDECAR_HIDDEN_IMPORTS)
        cli_imports = set(build_sidecar.CLI_HIDDEN_IMPORTS)

        self.assertIn("analyzer.ir", sidecar)
        self.assertIn("analyzer.ir", cli_imports)
        self.assertNotIn("scipy", sidecar)
        self.assertNotIn("scipy", cli_imports)
        self.assertTrue({"analyzer.gpc", "analyzer.mw", "analyzer.dsc", "analyzer.ir"} <= cli_imports)

    def test_build_executable_requires_explicit_hidden_imports(self):
        parameters = inspect.signature(build_sidecar.build_executable).parameters
        self.assertIn("hidden_imports", parameters)

    def test_python_requirements_do_not_include_unused_scipy(self):
        requirements = (PYTHON_DIR / "requirements.txt").read_text(encoding="utf-8")
        self.assertNotIn("scipy", requirements.casefold())


if __name__ == "__main__":
    unittest.main()
