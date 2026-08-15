#!/usr/bin/env python3
"""Smoke-test the packaged sidecar and CLI UTF-8 pipe contracts."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path

from build_sidecar import get_target_triple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BINARY_DIR = PROJECT_ROOT / "src-tauri" / "binaries"


def _binary_path(name: str) -> Path:
    suffix = ".exe" if platform.system() == "Windows" else ""
    path = BINARY_DIR / f"{name}-{get_target_triple()}{suffix}"
    if not path.is_file():
        raise RuntimeError(f"Packaged binary not found: {path}")
    return path


def _run(
    command: list[str],
    *,
    stdin_text: str | None = None,
) -> tuple[subprocess.CompletedProcess[bytes], str, str]:
    environment = os.environ.copy()
    # Exercise a legacy pipe encoding when the frozen runtime honors this
    # setting; the Windows matrix also covers that platform's native defaults.
    environment["PYTHONIOENCODING"] = "gbk"
    completed = subprocess.run(
        command,
        input=None if stdin_text is None else stdin_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
        timeout=120,
    )
    stdout = completed.stdout.decode("utf-8", errors="strict")
    stderr = completed.stderr.decode("utf-8", errors="strict")
    return completed, stdout, stderr


def _smoke_sidecar(sidecar: Path, data_dir: Path) -> None:
    request_id = "中文-pipe-smoke"
    request = {
        "jsonrpc": "2.0",
        "method": "gpc.list_files",
        "params": {"datadir": str(data_dir)},
        "id": request_id,
    }
    completed, stdout, stderr = _run(
        [str(sidecar)],
        stdin_text=json.dumps(request, ensure_ascii=False) + "\n",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Sidecar exited with {completed.returncode}: {stderr or stdout}"
        )

    messages = [json.loads(line) for line in stdout.splitlines() if line.strip()]
    response = next((item for item in messages if item.get("id") == request_id), None)
    if response is None:
        raise RuntimeError(f"Sidecar response missing from stdout: {stdout}")
    if response.get("result", {}).get("files") != ["样品.rst"]:
        raise RuntimeError(f"Unexpected sidecar response: {response}")


def _smoke_cli(cli: Path, missing_dir: Path) -> None:
    base_command = [
        str(cli),
        "gpc",
        "--quiet",
        "--datadir",
        str(missing_dir),
        "--output-name",
        "smoke",
    ]
    completed, stdout, stderr = _run([*base_command, "--json"])
    if completed.returncode != 2:
        raise RuntimeError(
            f"CLI JSON smoke returned {completed.returncode}: {stderr or stdout}"
        )
    payload = json.loads(stdout)
    if str(missing_dir) not in payload.get("error", ""):
        raise RuntimeError(f"CLI JSON output lost the Unicode path: {payload}")

    completed, stdout, stderr = _run(base_command)
    if completed.returncode != 2:
        raise RuntimeError(
            f"CLI stderr smoke returned {completed.returncode}: {stderr or stdout}"
        )
    if str(missing_dir) not in stderr:
        raise RuntimeError(f"CLI stderr output lost the Unicode path: {stderr}")


def main() -> None:
    sidecar = _binary_path("polyanalyzer-engine")
    cli = _binary_path("poly")
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = Path(temp_dir) / "中文目录"
        data_dir.mkdir()
        (data_dir / "样品.rst").write_text("smoke", encoding="utf-8")
        missing_dir = Path(temp_dir) / "不存在"
        _smoke_sidecar(sidecar, data_dir)
        _smoke_cli(cli, missing_dir)
    print("Packaged sidecar and CLI UTF-8 smoke tests passed")


if __name__ == "__main__":
    main()
