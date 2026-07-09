#!/usr/bin/env python3
"""Build PolyAnalyzer Python executables using PyInstaller.

Usage:
    python build_sidecar.py

Output:
    src-tauri/binaries/polyanalyzer-engine-{target_triple}[.exe]
    src-tauri/binaries/poly-{target_triple}[.exe]
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


HIDDEN_IMPORTS = [
    "numpy",
    "pandas",
    "matplotlib",
    "matplotlib.backends.backend_agg",
    "scipy",
    "openpyxl",
    "chardet",
    "plottable",
    "analyzer.gpc",
    "analyzer.mw",
    "analyzer.dsc",
    "analyzer.ir",
    "analyzer.plotting",
]

EXCLUDED_MODULES = [
    "tkinter",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "IPython",
    "jupyter",
    "streamlit",
]


def build_executable(
    *,
    python_dir: str,
    output_dir: str,
    target_triple: str,
    binary_name: str,
    entrypoint: str,
) -> str:
    """Build one PyInstaller executable and rename it for Tauri externalBin."""
    ext = ".exe" if platform.system() == "Windows" else ""
    output_name = f"{binary_name}-{target_triple}{ext}"
    final_path = os.path.join(output_dir, output_name)

    print(f"Building {binary_name} for: {target_triple}")
    print(f"Output: {final_path}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--name", binary_name,
        "--distpath", output_dir,
        "--workpath", os.path.join(python_dir, "build", binary_name),
        "--specpath", os.path.join(python_dir, "build"),
        "--paths", python_dir,
    ]
    for module in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", module])
    for module in EXCLUDED_MODULES:
        cmd.extend(["--exclude-module", module])
    cmd.append(os.path.join(python_dir, entrypoint))

    subprocess.run(cmd, check=True)

    # Rename to include target triple (Tauri sidecar naming convention)
    built_path = os.path.join(output_dir, f"{binary_name}{ext}")
    if os.path.exists(built_path) and built_path != final_path:
        shutil.move(built_path, final_path)

    size_mb = os.path.getsize(final_path) / (1024 * 1024)
    print(f"{binary_name} built: {final_path}  Size: {size_mb:.1f} MB\n")
    return final_path


def main() -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    python_dir = os.path.join(project_root, "python")
    output_dir = os.path.join(project_root, "src-tauri", "binaries")
    os.makedirs(output_dir, exist_ok=True)

    target_triple = get_target_triple()
    build_executable(
        python_dir=python_dir,
        output_dir=output_dir,
        target_triple=target_triple,
        binary_name="polyanalyzer-engine",
        entrypoint="main.py",
    )
    build_executable(
        python_dir=python_dir,
        output_dir=output_dir,
        target_triple=target_triple,
        binary_name="poly",
        entrypoint="cli.py",
    )


if __name__ == "__main__":
    main()
