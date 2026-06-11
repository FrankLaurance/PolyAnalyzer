---
name: polyanalyzer-cli
description: Implement, maintain, document, and verify the PolyAnalyzer batch CLI and its Tauri bundle integration. Use when working in the PolyAnalyzer repo on the `poly` command, GPC/Mw/DSC batch analysis, CLI docs, PyInstaller sidecar builds, or Tauri externalBin packaging.
---

# PolyAnalyzer CLI

## Quick Start

Use this skill in `/Users/frank/Desktop/python/PolyAnalyzer` when the task touches the `poly` CLI, its docs, or packaging.

Primary commands:

```bash
python3 python/cli.py --help
python3 python/cli.py gpc --datadir ./datapath --output-name test
python3 python/cli.py mw --datadir ./datapath --json --quiet
python3 python/cli.py dsc --datadir ./datapath
python3 python/cli.py clean --datadir ./datapath --yes
```

## Repo Map

- `python/cli.py` is the business CLI entrypoint for `poly`.
- `python/analyzer/` contains the reusable GPC, Mw, and DSC analyzers.
- `python/main.py` is the JSON-RPC sidecar for the Tauri UI; do not replace it with CLI behavior.
- `python/build_sidecar.py` builds both `polyanalyzer-engine-{target}` and `poly-{target}` with PyInstaller.
- `src-tauri/tauri.conf.json` must list both `binaries/polyanalyzer-engine` and `binaries/poly` under `bundle.externalBin`.
- `CLI_USAGE.md` and `CLI_USAGE_EN.md` are the user-facing CLI docs.

## CLI Contract

Keep these commands stable unless the user explicitly asks for a breaking change:

```bash
poly --version
poly gpc --datadir PATH --output-name NAME [--file A.rst ...] [--overwrite] [--no-csv] [--no-image] [--no-xlsx]
poly mw --datadir PATH [--file A.rst ...] [--setting NAME] [--segments 0,5000,... | --ranges 0-5000,5000-10000] [style options]
poly dsc --datadir PATH [--setting NAME] [--peaks-upward] [--center-peak] [--left-length 1.9] [--right-length 1.9] [style options]
poly clean --datadir PATH --yes
poly settings list|show|save|delete --type mw|dsc ...
```

Output rules:

- Default mode prints human-readable progress and result paths.
- `--json` writes machine-readable JSON to stdout and progress to stderr.
- `--quiet` suppresses progress.
- Exit codes are `0` success, `1` analysis/runtime failure, `2` argument error.
- Every GUI setting that has batch-processing meaning must have a CLI flag.
- `--setting` loads saved Mw/DSC defaults; explicit CLI flags override the setting file.

## Implementation Rules

- Reuse analyzer classes directly; do not route the CLI through JSON-RPC.
- Keep the Tauri UI sidecar protocol unchanged unless the user asks for UI integration.
- `clean` must only remove known sibling output directories: `Mw_output`, `GPC_output`, `DSC_Cycle`, `DSC_Pic`.
- Keep analyzer imports lazy enough that `poly --help` and `poly --version` do not initialize Matplotlib.
- For Mw range configuration, support both boundary points via `--segments` and continuous ranges via `--ranges`; ranges must be contiguous so no hidden intervals are created.
- Set writable cache env vars before analyzer imports when changing CLI or sidecar startup:
  - `MPLCONFIGDIR`
  - `XDG_CACHE_HOME`
- Do not register `poly` in global `PATH`; installed users call it from the app/install directory.

## Validation Checklist

Run the smallest relevant subset, and run the full list before release-like work:

```bash
python3 -m py_compile python/cli.py python/build_sidecar.py python/main.py python/api.py python/analyzer/__init__.py python/analyzer/base.py python/analyzer/gpc.py python/analyzer/mw.py python/analyzer/dsc.py
python3 python/cli.py --version
python3 python/cli.py gpc --help
python3 python/cli.py mw --help
python3 python/cli.py dsc --help
python3 python/cli.py mw --datadir datapath --file HR-D901B.rst --ranges 0-5000,5000-10000,10000-50000 --json --quiet
pnpm build
```

For functional smoke tests, copy sample files from `datapath/` into a temp directory and run:

```bash
python3 python/cli.py gpc --datadir /tmp/poly-test/datapath --output-name cli-gpc --file HR-D901B.rst --quiet
python3 python/cli.py mw --datadir /tmp/poly-test/datapath --file HR-D901B.rst --json --quiet
python3 python/cli.py dsc --datadir /tmp/poly-test/datapath --quiet
python3 python/cli.py clean --datadir /tmp/poly-test/datapath --yes --json --quiet
```

For packaging verification:

```bash
python3 python/build_sidecar.py
src-tauri/binaries/poly-aarch64-apple-darwin --version
pnpm tauri build --bundles app --no-sign
src-tauri/target/release/bundle/macos/PolyAnalyzer.app/Contents/MacOS/poly --help
```

PyInstaller-built binaries may need unsandboxed execution on macOS because the bootloader uses system semaphores.
