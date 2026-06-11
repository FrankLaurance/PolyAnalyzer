# PolyAnalyzer CLI Usage

`poly` is the PolyAnalyzer batch CLI for scripted GPC, Mw, and DSC analysis. It generates files and terminal output only; it does not open the desktop UI or preview images.

Rule: every desktop setting that matters for batch analysis should have a CLI argument. Saved Mw/DSC settings under `setting/` can be loaded with `--setting`; explicit CLI arguments override the setting file.

## Installation And Invocation

### Source Checkout

```bash
cd PolyAnalyzer
pip install -r python/requirements.txt
python3 python/cli.py --help
```

In source checkouts, replace `poly` in the examples with:

```bash
python3 python/cli.py
```

### Installed App Bundle

The CLI is bundled with the Tauri desktop installers, but it is not registered in the global `PATH`. Run it from the install directory or app resource directory:

| Platform | Typical path |
|----------|--------------|
| Windows | `C:\Program Files\PolyAnalyzer\poly.exe` or `poly.exe` under the user-selected install directory |
| macOS | `/Applications/PolyAnalyzer.app/Contents/MacOS/poly` |
| Linux deb | `/usr/lib/polyanalyzer/poly` or the package resource directory |
| Linux AppImage | `squashfs-root/usr/lib/polyanalyzer/poly` after extraction, or the runtime resource path inside the AppImage |

macOS example:

```bash
"/Applications/PolyAnalyzer.app/Contents/MacOS/poly" --help
```

## Common Output Options

Every business subcommand supports:

```bash
--json    # write machine-readable JSON to stdout; progress goes to stderr
--quiet   # suppress progress output
```

Exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Analysis failed or output already exists |
| `2` | Invalid arguments |

## GPC Analysis

The input directory must contain `.rst` files. Output is written to `GPC_output/` next to the data directory.

```bash
poly gpc --datadir ./datapath --output-name 20260328
```

Common usage:

```bash
poly gpc \
  --datadir ./datapath \
  --output-name batch-001 \
  --file HR-D901B.rst UH-D901D.rst \
  --overwrite
```

Options:

| Option | Description |
|--------|-------------|
| `--file NAME ...` | Process only selected `.rst` files; repeatable |
| `--overwrite` | Replace existing output with the same name |
| `--no-csv` | Do not write the GPC CSV summary |
| `--no-image` | Do not write the PNG image |
| `--no-xlsx` | Do not write the XLSX peak data |

Output files:

- `GPC_output/{output-name}.csv`
- `GPC_output/{output-name}.png`
- `GPC_output/{output-name}.xlsx`

## Mw Analysis

The input directory must contain `.rst` files. Output is written to `Mw_output/` next to the data directory.

```bash
poly mw --datadir ./datapath
```

Select files, segments, and styling:

```bash
poly mw \
  --datadir ./datapath \
  --file HR-D901B.rst \
  --segments 0,5000,10000,50000,100000,500000,1000000 \
  --bar-color '#002FA7' \
  --mw-color '#FF6A07' \
  --line-width 1.2
```

Define segments by continuous ranges:

```bash
poly mw \
  --datadir ./datapath \
  --ranges 0-5000,5000-10000,10000-50000,50000-100000
```

Load defaults from a setting file, then override selected values from the command line:

```bash
poly mw \
  --datadir ./datapath \
  --setting publication.json \
  --ranges 0-10000,10000-50000,50000-500000 \
  --no-table
```

Plot options:

| Option | Description |
|--------|-------------|
| `--setting NAME` | Load an Mw setting file from `setting/`; CLI arguments override it |
| `--segments 0,5000,...` | Increasing molecular-weight segment positions |
| `--ranges 0-5000,5000-10000` | Define continuous ranges; equivalent to boundaries `0,5000,10000` |
| `--no-image` | Do not write PNG images |
| `--draw-bar` / `--no-bar` | Draw or hide bars |
| `--draw-mw-curve` / `--no-mw-curve` | Draw or hide the Mw curve |
| `--draw-table` / `--no-table` | Draw or hide the data table |
| `--bar-color COLOR` | Bar color |
| `--mw-color COLOR` | Mw curve color |
| `--bar-width N` | Bar width multiplier |
| `--line-width N` | Curve line width |
| `--axis-width N` | Axis line width |
| `--title-font-size N` | Title font size |
| `--axis-font-size N` | Axis label font size |
| `--transparent-background` | Transparent background, default |
| `--opaque-background` | Opaque background |

Output files:

- `Mw_output/{sample-name}.png`

## DSC Analysis

The input directory must contain `.txt` files. Output is written to `DSC_Cycle/` and `DSC_Pic/` next to the data directory.

```bash
poly dsc --datadir ./datapath
```

Peak orientation and centering:

```bash
poly dsc \
  --datadir ./datapath \
  --setting defaultDSCSetting.ini \
  --peaks-upward \
  --center-peak \
  --left-length 1.9 \
  --right-length 1.9
```

Options:

| Option | Description |
|--------|-------------|
| `--setting NAME` | Load a DSC setting file from `setting/`; CLI arguments override it |
| `--peaks-upward` | Orient peaks upward |
| `--center-peak` | Center plots around detected peaks |
| `--left-length N` | Left trim length for each cycle |
| `--right-length N` | Right trim length for each cycle |
| `--no-segment-data` | Do not save segment CSV files |
| `--no-segment-plots` | Do not draw per-cycle images |
| `--no-cycle` | Do not draw cycle overlay plots |
| `--no-cycle-image` | Do not save cycle overlay images |
| `--curve-color COLOR` | Curve color |
| `--line-width N` | Curve line width |
| `--axis-width N` | Axis line width |
| `--title-font-size N` | Title font size |
| `--axis-font-size N` | Axis label font size |

Output files:

- `DSC_Cycle/Cycle*/{sample-name}.csv`
- `DSC_Cycle/Cycle*/result.png`
- `DSC_Pic/{sample-name}/Cycle *.png`

## Clean Output Directories

`clean` only removes known output directories next to the data directory: `Mw_output/`, `GPC_output/`, `DSC_Cycle/`, and `DSC_Pic/`. It requires `--yes`.

```bash
poly clean --datadir ./datapath --yes
```

## Settings Management

Settings are stored under `setting/` in the source checkout or install directory.

```bash
poly settings list --type mw
poly settings show --type mw --name defaultSetting.ini
poly settings show --type dsc --name defaultDSCSetting.ini --json
```

Save a setting:

```bash
poly settings save \
  --type mw \
  --name publication.json \
  --set bar_color='"#002FA7"' \
  --set line_width=1.2 \
  --set draw_table=true
```

Save from a JSON file:

```bash
poly settings save --type dsc --name dsc-blue.json --from-json ./dsc-blue.json
```

Delete a setting:

```bash
poly settings delete --type mw --name publication.json
```

## JSON Output Example

```bash
poly mw --datadir ./datapath --file HR-D901B.rst --json --quiet
```

Output:

```json
{
  "success": true,
  "message": "Mw analysis complete",
  "output_dir": "/path/to/Mw_output",
  "files": ["HR-D901B.rst"]
}
```

## FAQ

**Why does `poly` not work from any terminal after installation?**  
This version does not register a global `PATH` entry. Use the full path to the bundled CLI.

**What if output already exists?**  
Use `--overwrite` for GPC outputs with the same name. Mw and DSC overwrite files by sample name.

**Does the CLI open the graphical app?**  
No. It processes data, writes files, and prints result paths.
