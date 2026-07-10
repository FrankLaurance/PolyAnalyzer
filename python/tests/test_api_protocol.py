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

# Keep the legacy import-time logger away from the repository while RED tests run.
_IMPORT_TMP = tempfile.TemporaryDirectory()
_ORIGINAL_CWD = os.getcwd()
os.chdir(_IMPORT_TMP.name)
os.environ["POLYANALYZER_DISABLE_FILE_LOG"] = "1"
try:
    import api
finally:
    os.environ.pop("POLYANALYZER_DISABLE_FILE_LOG", None)
    os.chdir(_ORIGINAL_CWD)


class JsonRpcProtocolTests(unittest.TestCase):
    def _handle_line(self, payload):
        output = io.StringIO()
        with patch.object(api.sys, "stdout", output):
            api.handle_line(json.dumps(payload))
        return json.loads(output.getvalue())

    def test_non_object_request_returns_invalid_request(self):
        response = self._handle_line(1)
        self.assertEqual(api.INVALID_REQUEST, response["error"]["code"])
        self.assertIsNone(response["id"])

    def test_empty_batch_returns_invalid_request(self):
        response = self._handle_line([])
        self.assertEqual(api.INVALID_REQUEST, response["error"]["code"])
        self.assertIsNone(response["id"])

    def test_invalid_batch_item_returns_invalid_request_without_aborting_batch(self):
        response = self._handle_line([
            1,
            {"jsonrpc": "2.0", "method": "missing", "id": 7},
        ])
        self.assertEqual(2, len(response))
        self.assertEqual(api.INVALID_REQUEST, response[0]["error"]["code"])
        self.assertEqual(api.METHOD_NOT_FOUND, response[1]["error"]["code"])

    def test_progress_notification_identifies_analyzer_and_request(self):
        original_params = {"value": 3}

        def handler(params):
            callback = api._make_progress_callback(params, "mw")
            callback(0.5, "working")
            return {"ok": True}

        notifications = []
        with patch.dict(api.METHOD_TABLE, {"test.progress": handler}, clear=False):
            with patch.object(api, "send_notification", side_effect=lambda method, params: notifications.append((method, params))):
                response = api._handle_request({
                    "jsonrpc": "2.0",
                    "method": "test.progress",
                    "params": original_params,
                    "id": "req-4",
                })

        self.assertEqual({"value": 3}, original_params)
        self.assertEqual({"ok": True}, response["result"])
        self.assertEqual("progress", notifications[0][0])
        self.assertEqual("mw", notifications[0][1]["analyzer"])
        self.assertEqual("req-4", notifications[0][1]["request_id"])


class ApiFilesystemTests(unittest.TestCase):
    def test_file_listing_returns_regular_files_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "sample.rst").write_text("data", encoding="utf-8")
            Path(temp_dir, "folder.rst").mkdir()

            files = api._list_files_with_suffix(temp_dir, ".rst")

        self.assertEqual(["sample.rst"], files)

    def test_clean_output_requires_confirmation_and_existing_datadir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir, "data")
            data_dir.mkdir()

            with self.assertRaises(api.JsonRpcError) as missing_confirmation:
                api._system_clean_output({"datadir": str(data_dir)})
            self.assertEqual(api.INVALID_PARAMS, missing_confirmation.exception.code)

            with self.assertRaises(api.JsonRpcError) as missing_datadir:
                api._system_clean_output({
                    "datadir": str(Path(temp_dir, "missing")),
                    "confirm": True,
                })
            self.assertEqual(api.INVALID_PARAMS, missing_datadir.exception.code)

    def test_clean_output_only_recreates_known_direct_siblings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            data_dir = root / "data"
            data_dir.mkdir()
            known = ["Mw_output", "GPC_output", "DSC_Cycle", "DSC_Pic"]
            for name in known:
                output = root / name
                output.mkdir()
                (output / "old.txt").write_text("old", encoding="utf-8")
            app_data = root / "app-data"
            ir_output = app_data / "IR_output"
            ir_output.mkdir(parents=True)
            (ir_output / "old.txt").write_text("old", encoding="utf-8")
            unrelated = root / "unrelated"
            unrelated.mkdir()
            (unrelated / "keep.txt").write_text("keep", encoding="utf-8")

            with patch.object(api, "get_install_dir", return_value=str(app_data)):
                result = api._system_clean_output({
                    "datadir": str(data_dir),
                    "confirm": True,
                })

            self.assertEqual(
                {
                    *(str((root / name).resolve()) for name in known),
                    str(ir_output.resolve()),
                },
                {str(Path(path).resolve()) for path in result["cleaned"]},
            )
            for name in known:
                self.assertTrue((root / name).is_dir())
                self.assertEqual([], list((root / name).iterdir()))
            self.assertTrue(ir_output.is_dir())
            self.assertEqual([], list(ir_output.iterdir()))
            self.assertEqual("keep", (unrelated / "keep.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
