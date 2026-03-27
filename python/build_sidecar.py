#!/usr/bin/env python3
"""Build the Python sidecar executable using PyInstaller.

Usage:
    python build_sidecar.py

Output:
    src-tauri/binaries/polyanalyzer-engine-{target_triple}[.exe]
"""

import os
import platform
import subprocess
import sys
import shutil


def get_target_triple() -> str:
    """Get the Rust-style target triple for the current platform."""
    machine = platform.machine().lower()
    system = platform.system().lower()

    arch_map = {
        "x86_64": "x86_64",
        "amd64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }
    arch = arch_map.get(machine, machine)

    if system == "windows":
        return f"{arch}-pc-windows-msvc"
    elif system == "linux":
        return f"{arch}-unknown-linux-gnu"
    elif system == "darwin":
        return f"{arch}-apple-darwin"
    else:
        raise RuntimeError(f"Unsupported platform: {system} {machine}")


def main() -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    python_dir = os.path.join(project_root, "python")
    output_dir = os.path.join(project_root, "src-tauri", "binaries")
    os.makedirs(output_dir, exist_ok=True)

    target_triple = get_target_triple()
    ext = ".exe" if platform.system() == "Windows" else ""
    output_name = f"polyanalyzer-engine-{target_triple}{ext}"

    print(f"Building sidecar for: {target_triple}")
    print(f"Output: {os.path.join(output_dir, output_name)}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--name", "polyanalyzer-engine",
        "--distpath", output_dir,
        "--workpath", os.path.join(python_dir, "build"),
        "--specpath", os.path.join(python_dir, "build"),
        "--paths", python_dir,
        "--hidden-import", "numpy",
        "--hidden-import", "pandas",
        "--hidden-import", "matplotlib",
        "--hidden-import", "matplotlib.backends.backend_agg",
        "--hidden-import", "scipy",
        "--hidden-import", "openpyxl",
        "--hidden-import", "chardet",
        "--exclude-module", "tkinter",
        "--exclude-module", "PyQt5",
        "--exclude-module", "PyQt6",
        "--exclude-module", "PySide2",
        "--exclude-module", "PySide6",
        "--exclude-module", "IPython",
        "--exclude-module", "jupyter",
        "--exclude-module", "streamlit",
        os.path.join(python_dir, "main.py"),
    ]

    subprocess.run(cmd, check=True)

    # Rename to include target triple (Tauri sidecar naming convention)
    built_path = os.path.join(output_dir, f"polyanalyzer-engine{ext}")
    final_path = os.path.join(output_dir, output_name)
    if os.path.exists(built_path) and built_path != final_path:
        shutil.move(built_path, final_path)

    print(f"\n✅ Sidecar built: {final_path}")
    size_mb = os.path.getsize(final_path) / (1024 * 1024)
    print(f"   Size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
