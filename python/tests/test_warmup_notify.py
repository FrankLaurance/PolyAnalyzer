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


if __name__ == "__main__":
    unittest.main()
