# PolyAnalyzer 2.2.1

[中文](README.md)

PolyAnalyzer is a Tauri v2, React, and Python sidecar desktop application for polymer characterization data.

## Features

| Module | Input | Main outputs |
|--------|-------|--------------|
| GPC | `.rst` | Molecular-weight summary, chromatogram, and peak data |
| Mw | `.rst` | Molecular-weight distribution plots and interval statistics |
| DSC | `.txt` | Segmented data, segment plots, and cycle comparisons |
| IR | `.dpt` | Red individual spectra, optional peak-normalized overlay, and manifest |

The React frontend communicates with the Python sidecar over stdin/stdout JSON-RPC. Progress notifications include an analyzer and request ID so tab activity remains isolated.

## Quick Start

### Requirements

- Node.js 20+
- pnpm 9+
- Stable Rust toolchain
- Python 3.11+
- [Tauri v2 system prerequisites](https://v2.tauri.app/start/prerequisites/) for the host platform

### Run from source

```bash
git clone https://github.com/FrankLaurance/PolyAnalyzer.git
cd PolyAnalyzer

python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install -r python/requirements.txt
python -m pip install -r python/requirements-build.txt
pnpm install

python python/build_sidecar.py
pnpm tauri dev
```

`python/build_sidecar.py` creates the platform-specific `polyanalyzer-engine` and `poly` sidecars required by Tauri. Build the sidecars before starting or packaging the desktop app.

## Validation

```bash
python -m unittest discover -s python/tests -p "test_*.py"
pnpm test
pnpm build
python python/build_sidecar.py
cargo check --manifest-path src-tauri/Cargo.toml
cargo test --manifest-path src-tauri/Cargo.toml
```

## Packaging

```bash
python python/build_sidecar.py
pnpm tauri build
```

`bundle.targets` is set to `all`, producing formats supported by the current host: MSI/NSIS on Windows, deb/AppImage on Linux, and app/dmg on macOS.

## Version Synchronization

```bash
./release.sh 2.2.1
```

The script synchronizes version fields only. It does not create a commit, Git tag, or GitHub Release. It updates:

- `package.json`
- `src-tauri/tauri.conf.json`
- `src-tauri/Cargo.toml`
- `src-tauri/Cargo.lock`
- `python/analyzer/base.py`

For tag builds, GitHub Actions removes the leading `v` from `vX.Y.Z` and runs this script before tests and packaging.

## Command Line

Use the Python CLI directly from a source checkout:

```bash
python python/cli.py --help
```

The CLI covers GPC, Mw, DSC, and IR. See [CLI_USAGE_EN.md](CLI_USAGE_EN.md) or [CLI_USAGE.md](CLI_USAGE.md) for the complete command reference.

The desktop app and CLI share Analysis Profiles under `setting/profiles/{mw,dsc,ir}/`. Legacy defaults migrate automatically; the desktop keeps a localStorage cache and synchronizes named profiles after connecting to the sidecar.

## Output Locations

- GPC: `GPC_output/` next to the selected data directory
- Mw: `Mw_output/` next to the selected data directory
- DSC: `DSC_Cycle/` and `DSC_Pic/` next to the selected data directory
- IR: `IR_output/` under the writable application data root

In development, the writable data root is the repository. Packaged applications use the operating system's PolyAnalyzer user-data directory.

## Project Layout

```text
src/                    React frontend
src-tauri/              Tauri/Rust application and capabilities
python/                 JSON-RPC sidecar, analyzers, and CLI
python/tests/           Python unittest suite
.github/workflows/      Multi-platform build and release workflow
release.sh              Version synchronization script
```

See [MANUAL.md](MANUAL.md) for user instructions and [DEV_TOOLS.md](DEV_TOOLS.md) for development setup.

## License

[MIT](LICENSE)
