#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: ./release.sh <major.minor.patch>" >&2
  exit 1
fi

VERSION="${1#v}"
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Invalid semantic version: $1" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

python3 - "$VERSION" <<'PY'
import json
import re
import sys
from pathlib import Path

version = sys.argv[1]
root = Path.cwd()

for relative_path in ("package.json", "src-tauri/tauri.conf.json"):
    path = root / relative_path
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = version
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

replacements = (
    (
        root / "src-tauri/Cargo.toml",
        r'(?ms)(\[package\].*?^version = ")[^"]+("$)',
        rf'\g<1>{version}\g<2>',
    ),
    (
        root / "src-tauri/Cargo.lock",
        r'(?m)(^name = "polyanalyzer"\nversion = ")[^"]+("$)',
        rf'\g<1>{version}\g<2>',
    ),
    (
        root / "python/analyzer/base.py",
        r'(?m)(^APP_VERSION: str = ")[^"]+("$)',
        rf'\g<1>{version}\g<2>',
    ),
)

for path, pattern, replacement in replacements:
    original = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, replacement, original, count=1)
    if count != 1:
        raise SystemExit(f"Could not update version in {path}")
    path.write_text(updated, encoding="utf-8")
PY

echo "PolyAnalyzer version synchronized to $VERSION"
