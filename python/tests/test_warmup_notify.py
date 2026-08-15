"""
Tests for the sidecar warmup status notifications shown as a banner in the GUI.
"""

import contextlib
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

# Keep the legacy import-time logger away from the repository while tests run.
_IMPORT_TMP = tempfile.TemporaryDirectory()
_ORIGINAL_CWD = os.getcwd()
os.chdir(_IMPORT_TMP.name)
os.environ["POLYANALYZER_DISABLE_FILE_LOG"] = "1"
try:
    import main
finally:
    os.environ.pop("POLYANALYZER_DISABLE_FILE_LOG", None)
    os.chdir(_ORIGINAL_CWD)


class WarmupNotificationTests(unittest.TestCase):
    def _capture_notification(self, progress: float, message: str) -> dict:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            main._notify_warmup(progress, message)
        line = stdout.getvalue().strip()
        self.assertTrue(line, "notification must write exactly one line")
        return json.loads(line)

    def test_warming_notification_carries_warmup_marker(self) -> None:
        msg = self._capture_notification(0.0, "引擎预热中…")

        self.assertEqual("2.0", msg["jsonrpc"])
        self.assertEqual("progress", msg["method"])
        self.assertNotIn("id", msg)
        self.assertTrue(msg["params"]["warmup"])
        self.assertEqual(0.0, msg["params"]["progress"])
        self.assertEqual("引擎预热中…", msg["params"]["message"])

    def test_ready_notification_reports_full_progress(self) -> None:
        msg = self._capture_notification(100.0, "引擎预热完成")

        self.assertTrue(msg["params"]["warmup"])
        self.assertEqual(100.0, msg["params"]["progress"])


class SidecarStandardStreamTests(unittest.TestCase):
    def test_sidecar_protocol_reconfigures_non_utf8_pipes(self) -> None:
        request = {"jsonrpc": "2.0", "id": 1, "params": {"path": "C:\\中文目录"}}
        stdin_bytes = io.BytesIO(
            (json.dumps(request, ensure_ascii=False) + "\n").encode("utf-8")
        )
        stdout_bytes = io.BytesIO()
        stderr_bytes = io.BytesIO()
        stdin = io.TextIOWrapper(stdin_bytes, encoding="gbk")
        # Explicit CRLF translation reproduces Windows pipe behavior even when
        # this test runs on Linux or macOS.
        stdout = io.TextIOWrapper(stdout_bytes, encoding="gbk", newline="\r\n")
        stderr = io.TextIOWrapper(stderr_bytes, encoding="gbk", newline="\r\n")

        with (
            patch.object(main.sys, "stdin", stdin),
            patch.object(main.sys, "stdout", stdout),
            patch.object(main.sys, "stderr", stderr),
        ):
            main._configure_standard_streams()
            self.assertEqual("utf-8", main.sys.stdin.encoding)
            self.assertEqual("strict", main.sys.stdin.errors)
            self.assertEqual("utf-8", main.sys.stdout.encoding)
            self.assertEqual("strict", main.sys.stdout.errors)
            self.assertEqual("utf-8", main.sys.stderr.encoding)
            self.assertEqual("backslashreplace", main.sys.stderr.errors)
            decoded_request = json.loads(main.sys.stdin.readline())
            main._notify_warmup(0.0, "引擎预热中…")
            main.sys.stderr.write("中文日志\n")
            main.sys.stdout.flush()
            main.sys.stderr.flush()

        self.assertEqual(request, decoded_request)
        notification = json.loads(stdout_bytes.getvalue().decode("utf-8"))
        self.assertEqual("引擎预热中…", notification["params"]["message"])
        self.assertEqual(
            ["中文日志"],
            stderr_bytes.getvalue().decode("utf-8").splitlines(),
        )


if __name__ == "__main__":
    unittest.main()
