"""
GPC Excel export reader — parses instrument Excel workbooks into per-sample data.

Supported layout (auto-detected, any number of sample columns):

- A data sheet whose header row contains ``LogM`` columns paired with value
  columns named ``<sample name> MMD`` (dw/dlogM) and/or
  ``<sample name> Cumulative`` (cumulative weight fraction, 0..1).
- An optional conventional results sheet with ``Mw (g/mol)``, ``Mn (g/mol)``,
  ``Mz (g/mol)``, ``Mz1 (g/mol)``, ``Mv (g/mol)``, ``Mp (g/mol)`` and
  ``Mw / Mn`` summary columns, sample names in the first column.

Missing MMD or Cumulative columns are derived from the other series.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np
import pandas as pd

VALUE_COLUMN_RE = re.compile(
    r"^(?P<name>.+?)\s+(?P<kind>MMD|dW/dlogM|Cumulative)$", re.IGNORECASE
)

_RESULTS_HEADER_ALIASES: Dict[str, str] = {
    "mw (g/mol)": "Mw",
    "mn (g/mol)": "Mn",
    "mp (g/mol)": "Mp",
    "mz (g/mol)": "Mz",
    "mz1 (g/mol)": "Mz+1",
    "mz+1 (g/mol)": "Mz+1",
    "mv (g/mol)": "Mv",
    "mw / mn": "PD",
    "pd": "PD",
}


@dataclass
class GpcExcelSample:
    """One sample extracted from a GPC Excel export."""

    name: str
    logm: np.ndarray = field(default_factory=lambda: np.array([]))
    mmd: np.ndarray = field(default_factory=lambda: np.array([]))
    cumulative: np.ndarray = field(default_factory=lambda: np.array([]))
    results: Dict[str, float] = field(default_factory=dict)


def _is_logm_header(cell: object) -> bool:
    return isinstance(cell, str) and cell.strip().casefold() == "logm"


def _parse_float(value: object) -> Optional[float]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    text = str(value).strip().replace(",", "").replace(" ", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def format_result(value: object) -> str:
    """Format a numeric result for CSV output without a trailing .0."""
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return str(int(number))
    return str(number)


def _derive_cumulative(logm: np.ndarray, mmd: np.ndarray) -> np.ndarray:
    """Cumulative weight fraction from dw/dlogM using slice widths."""
    widths = np.empty_like(logm)
    widths[1:-1] = (logm[2:] - logm[:-2]) / 2.0
    widths[0] = logm[1] - logm[0]
    widths[-1] = logm[-1] - logm[-2]
    weights = mmd * widths
    total = float(np.sum(weights))
    if total <= 0:
        raise ValueError("MMD 列积分为零，无法计算累积分布")
    return np.cumsum(weights) / total


def _derive_mmd(logm: np.ndarray, cumulative: np.ndarray) -> np.ndarray:
    """dw/dlogM from the cumulative weight fraction.

    The export may accumulate from either end of the distribution, so the
    cumulative series can be decreasing in ascending-logM order; dw/dlogM
    is the magnitude of the slope.
    """
    return np.abs(np.gradient(cumulative, logm))


def _read_data_sheet(df: pd.DataFrame) -> Dict[str, GpcExcelSample]:
    """Detect LogM/MMD/Cumulative column groups in a DataFrame sheet."""
    header_row = None
    for row_idx in range(min(len(df), 20)):
        row = [df.iat[row_idx, col] for col in range(df.shape[1])]
        if any(_is_logm_header(cell) for cell in row):
            header_row = row_idx
            break
    if header_row is None:
        return {}

    headers = [df.iat[header_row, col] for col in range(df.shape[1])]

    # Pair every value column with the nearest LogM column to its left.
    raw_series: Dict[str, Dict[str, np.ndarray]] = {}
    last_logm_col: Optional[int] = None
    for col, header in enumerate(headers):
        if _is_logm_header(header):
            last_logm_col = col
            continue
        if not isinstance(header, str):
            continue
        match = VALUE_COLUMN_RE.match(header.strip())
        if not match or last_logm_col is None:
            continue
        kind = match.group("kind").casefold()
        if kind == "dw/dlogm":
            kind = "mmd"
        name = match.group("name").strip()

        values = df.iloc[header_row + 1:, [last_logm_col, col]]
        values.columns = ["logm", "value"]
        values["logm"] = values["logm"].apply(_parse_float)
        values["value"] = values["value"].apply(_parse_float)
        values = values.dropna()
        if values.empty:
            continue

        logm = values["logm"].to_numpy(dtype=float)
        value = values["value"].to_numpy(dtype=float)
        # Sort ascending by logM so cumulative diffing is well-defined.
        order = np.argsort(logm)
        logm, value = logm[order], value[order]

        sample = raw_series.setdefault(
            name, GpcExcelSample(name=name)
        )
        sample.logm = logm
        sample.__dict__[kind] = value

    # Derive whichever distribution series is missing.
    for sample in raw_series.values():
        if sample.mmd.size == 0:
            if sample.cumulative.size == 0:
                continue
            sample.mmd = _derive_mmd(sample.logm, sample.cumulative)
        if sample.cumulative.size == 0:
            sample.cumulative = _derive_cumulative(sample.logm, sample.mmd)

    return {
        name: sample
        for name, sample in raw_series.items()
        if sample.mmd.size > 0 and sample.cumulative.size > 0
    }


def _read_results_sheet(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Detect the conventional results summary table in a DataFrame sheet."""
    header_row = None
    for row_idx in range(min(len(df), 20)):
        row = [df.iat[row_idx, col] for col in range(df.shape[1])]
        for cell in row:
            if isinstance(cell, str):
                folded = cell.strip().casefold()
                if folded.startswith("mw (g/mol)") or folded == "mw":
                    header_row = row_idx
                    break
        if header_row is not None:
            break
    if header_row is None:
        return {}

    headers = [df.iat[header_row, col] for col in range(df.shape[1])]
    column_map: Dict[int, str] = {}
    for col, cell in enumerate(headers):
        if not isinstance(cell, str):
            continue
        folded = cell.strip().casefold()
        for alias, canonical in _RESULTS_HEADER_ALIASES.items():
            if folded == alias or folded.startswith(alias + " "):
                column_map[col] = canonical
                break

    results: Dict[str, Dict[str, float]] = {}
    for row_idx in range(header_row + 1, len(df)):
        name_cell = df.iat[row_idx, 0]
        if not isinstance(name_cell, str) or not name_cell.strip():
            continue
        name = name_cell.strip()
        sample_results: Dict[str, float] = {}
        for col, canonical in column_map.items():
            parsed = _parse_float(df.iat[row_idx, col])
            if parsed is not None:
                sample_results[canonical] = parsed
        if "PD" not in sample_results and "Mw" in sample_results and "Mn" in sample_results:
            if sample_results["Mn"] != 0:
                sample_results["PD"] = sample_results["Mw"] / sample_results["Mn"]
        if sample_results:
            results[name] = sample_results
    return results


def parse_gpc_excel(path: str) -> Dict[str, GpcExcelSample]:
    """Parse a GPC Excel export into per-sample data.

    Returns:
        Mapping of sample name to :class:`GpcExcelSample`, insertion-ordered.

    Raises:
        ValueError: if no recognizable GPC data sheet is found.
    """
    sheets = pd.read_excel(path, sheet_name=None, header=None)
    if not sheets:
        raise ValueError(f"Excel 文件没有可读的工作表: {path}")

    samples: Dict[str, GpcExcelSample] = {}
    results_by_name: Dict[str, Dict[str, float]] = {}

    for df in sheets.values():
        if not samples:
            samples = _read_data_sheet(df)
        results_by_name.update(_read_results_sheet(df))

    if not samples:
        raise ValueError(
            f"未在 Excel 文件中识别到 GPC 数据（需要 LogM 与 MMD/Cumulative 列）: {path}"
        )

    for name, results in results_by_name.items():
        if name in samples:
            samples[name].results = results

    return samples
