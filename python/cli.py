#!/usr/bin/env python3
"""Business CLI for PolyAnalyzer batch analysis."""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import sys
import tempfile
from typing import Any, Callable

_CACHE_ROOT = os.path.join(tempfile.gettempdir(), "polyanalyzer-cache")
_MPL_CACHE_DIR = os.path.join(_CACHE_ROOT, "matplotlib")
_XDG_CACHE_DIR = os.path.join(_CACHE_ROOT, "xdg")
os.makedirs(_MPL_CACHE_DIR, exist_ok=True)
os.makedirs(_XDG_CACHE_DIR, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", _MPL_CACHE_DIR)
os.environ.setdefault("XDG_CACHE_HOME", _XDG_CACHE_DIR)

from analyzer import (
    APP_VERSION,
    DEFAULT_BAR_COLOR,
    DEFAULT_DSC_SETTING_NAME,
    DEFAULT_MW_COLOR,
    DEFAULT_SETTING_NAME,
    DEFAULT_TRANSPARENT_BACK,
    SettingsManager,
    get_install_dir,
)

EXIT_OK = 0
EXIT_ANALYSIS_FAILED = 1
EXIT_ARGUMENT_ERROR = 2


class CliError(Exception):
    """CLI failure with a stable exit code."""

    def __init__(self, message: str, exit_code: int = EXIT_ANALYSIS_FAILED) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


def _flatten_files(values: list[list[str]] | None) -> list[str] | None:
    if not values:
        return None
    return [item for group in values for item in group]


def _ensure_datadir(path: str) -> str:
    datadir = os.path.abspath(path)
    if not os.path.isdir(datadir):
        raise CliError(f"Data directory does not exist: {datadir}", EXIT_ARGUMENT_ERROR)
    return datadir


def _list_files(datadir: str, pattern: str) -> list[str]:
    return sorted(os.path.basename(path) for path in glob.glob(os.path.join(datadir, pattern)))


def _validate_selected_files(datadir: str, files: list[str] | None, pattern: str) -> list[str]:
    selected = files or _list_files(datadir, pattern)
    if not selected:
        raise CliError(f"No input files matching {pattern} were found in {datadir}")

    missing = [name for name in selected if not os.path.isfile(os.path.join(datadir, name))]
    if missing:
        raise CliError(
            "Input file(s) not found in data directory: " + ", ".join(missing),
            EXIT_ARGUMENT_ERROR,
        )
    return selected


def _parse_segments(value: str) -> list[int]:
    try:
        segments = [int(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("segments must be comma-separated integers") from exc
    if len(segments) < 2:
        raise argparse.ArgumentTypeError("segments must contain at least two positions")
    if segments != sorted(segments):
        raise argparse.ArgumentTypeError("segments must be sorted from low to high")
    return segments


def _parse_ranges(value: str) -> list[int]:
    ranges: list[tuple[int, int]] = []
    for raw_part in re.split(r"[,;]", value):
        part = raw_part.strip()
        if not part:
            continue
        match = re.fullmatch(r"(\d+)\s*(?:-|\.\.|:|~)\s*(\d+)", part)
        if not match:
            raise argparse.ArgumentTypeError(
                "ranges must look like START-END,START-END"
            )
        start = int(match.group(1))
        end = int(match.group(2))
        if start >= end:
            raise argparse.ArgumentTypeError("each range must satisfy START < END")
        ranges.append((start, end))

    if not ranges:
        raise argparse.ArgumentTypeError("ranges must contain at least one range")

    ranges.sort(key=lambda item: item[0])
    boundaries = [ranges[0][0]]
    previous_end = ranges[0][1]
    boundaries.append(previous_end)
    for start, end in ranges[1:]:
        if start != previous_end:
            raise argparse.ArgumentTypeError(
                "ranges must be continuous; use --segments for non-contiguous boundaries"
            )
        boundaries.append(end)
        previous_end = end
    return boundaries


def _resolve_setting_value(
    args: argparse.Namespace,
    attr: str,
    setting: dict[str, Any],
    key: str,
    fallback: Any,
) -> Any:
    value = getattr(args, attr)
    if value is not None:
        return value
    if key in setting and setting[key] is not None:
        return setting[key]
    return fallback


def _parse_setting_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _parse_set_items(items: list[str] | None) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for item in items or []:
        if "=" not in item:
            raise CliError(f"Invalid --set value, expected KEY=VALUE: {item}", EXIT_ARGUMENT_ERROR)
        key, raw_value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise CliError(f"Invalid --set key: {item}", EXIT_ARGUMENT_ERROR)
        parsed[key] = _parse_setting_value(raw_value.strip())
    return parsed


def _progress_callback(args: argparse.Namespace) -> Callable[[float, str], None] | None:
    if getattr(args, "quiet", False):
        return None

    stream = sys.stderr if getattr(args, "json", False) else sys.stdout

    def callback(progress: float, message: str) -> None:
        pct = max(0.0, min(100.0, progress * 100.0))
        print(f"[{pct:6.2f}%] {message}", file=stream)

    return callback


def _emit_result(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if payload.get("success"):
        print("Success")
    else:
        print("Failed", file=sys.stderr)

    message = payload.get("message")
    if message:
        stream = sys.stdout if payload.get("success") else sys.stderr
        print(message, file=stream)

    for key in ("output_dir", "cycle_dir", "pic_dir"):
        value = payload.get(key)
        if value:
            print(f"{key}: {value}")

    cleaned = payload.get("cleaned")
    if cleaned:
        print("cleaned:")
        for path in cleaned:
            print(f"  {path}")


def _default_settings(kind: str) -> tuple[str, dict[str, Any]]:
    if kind == "dsc":
        return DEFAULT_DSC_SETTING_NAME, {
            "curve_color": DEFAULT_BAR_COLOR,
            "transparent_back": DEFAULT_TRANSPARENT_BACK,
            "line_width": 1.0,
            "axis_width": 1.0,
            "title_font_size": 20,
            "axis_font_size": 14,
        }

    return DEFAULT_SETTING_NAME, {
        "segmentpos": [0, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000, 10000000, 50000000],
        "bar_color": DEFAULT_BAR_COLOR,
        "mw_color": DEFAULT_MW_COLOR,
        "transparent_back": DEFAULT_TRANSPARENT_BACK,
        "bar_width": 1.2,
        "line_width": 1.0,
        "axis_width": 1.0,
        "title_font_size": 20,
        "axis_font_size": 14,
        "draw_bar": True,
        "draw_mw": True,
        "draw_table": True,
    }


def _settings_manager(kind: str) -> SettingsManager:
    default_name, default_content = _default_settings(kind)
    return SettingsManager(
        os.path.join(get_install_dir(), "setting"),
        default_name,
        default_content,
    )


def _clean_setting(kind: str, setting: dict[str, Any]) -> dict[str, Any]:
    _default_name, default_content = _default_settings(kind)
    allowed_keys = set(default_content)
    return {
        key: value
        for key, value in setting.items()
        if key in allowed_keys and value is not None
    }


def _read_json_file(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise CliError(f"JSON file does not exist: {path}", EXIT_ARGUMENT_ERROR) from exc
    except json.JSONDecodeError as exc:
        raise CliError(f"Invalid JSON file: {path}", EXIT_ARGUMENT_ERROR) from exc

    if not isinstance(data, dict):
        raise CliError("Settings JSON must be an object", EXIT_ARGUMENT_ERROR)
    return data


def _run_gpc(args: argparse.Namespace) -> int:
    from analyzer import GPCAnalyzer

    datadir = _ensure_datadir(args.datadir)
    selected_files = _validate_selected_files(datadir, _flatten_files(args.files), "*.rst")

    analyzer = GPCAnalyzer(
        datadir=datadir,
        output_filename=args.output_name,
        save_file=args.save_csv,
        save_picture=args.save_image,
        display_mode=False,
        save_figure_file_gpc=args.save_xlsx,
        progress_callback=_progress_callback(args),
    )
    analyzer.selected_file = selected_files

    if analyzer.check_dir() and not args.overwrite:
        raise CliError(
            "Output files already exist. Re-run with --overwrite to replace them."
        )

    success = analyzer.run()
    if not success:
        raise CliError("GPC analysis failed")

    _emit_result(args, {
        "success": True,
        "message": "GPC analysis complete",
        "output_dir": analyzer.output_dir,
        "files": selected_files,
    })
    return EXIT_OK


def _run_mw(args: argparse.Namespace) -> int:
    from analyzer import MolecularWeightAnalyzer

    datadir = _ensure_datadir(args.datadir)
    selected_files = _validate_selected_files(datadir, _flatten_files(args.files), "*.rst")
    setting_name = args.setting or DEFAULT_SETTING_NAME
    setting = _clean_setting("mw", _settings_manager("mw").load_setting(setting_name))
    segments = args.ranges or args.segments or setting.get(
        "segmentpos",
        _default_settings("mw")[1]["segmentpos"],
    )

    analyzer = MolecularWeightAnalyzer(
        datadir=datadir,
        save_file=True,
        save_picture=args.save_image,
        display_picture=False,
        bar_color=_resolve_setting_value(args, "bar_color", setting, "bar_color", DEFAULT_BAR_COLOR),
        mw_color=_resolve_setting_value(args, "mw_color", setting, "mw_color", DEFAULT_MW_COLOR),
        bar_width=_resolve_setting_value(args, "bar_width", setting, "bar_width", 1.2),
        line_width=_resolve_setting_value(args, "line_width", setting, "line_width", 1.0),
        axis_width=_resolve_setting_value(args, "axis_width", setting, "axis_width", 1.0),
        title_font_size=_resolve_setting_value(args, "title_font_size", setting, "title_font_size", 20),
        axis_font_size=_resolve_setting_value(args, "axis_font_size", setting, "axis_font_size", 14),
        transparent_back=_resolve_setting_value(args, "transparent_back", setting, "transparent_back", DEFAULT_TRANSPARENT_BACK),
        draw_bar=_resolve_setting_value(args, "draw_bar", setting, "draw_bar", True),
        draw_mw=_resolve_setting_value(args, "draw_mw", setting, "draw_mw", True),
        draw_table=_resolve_setting_value(args, "draw_table", setting, "draw_table", True),
        setting_name=setting_name,
        progress_callback=_progress_callback(args),
    )
    analyzer.selected_file = selected_files
    analyzer.segmentpos = list(segments)
    analyzer.selectedpos = list(segments)
    analyzer.segmentnum = len(segments)

    success = analyzer.run()
    if not success:
        raise CliError("Mw analysis failed")

    _emit_result(args, {
        "success": True,
        "message": "Mw analysis complete",
        "output_dir": analyzer.output_dir,
        "files": selected_files,
        "segments": list(segments),
    })
    return EXIT_OK


def _run_dsc(args: argparse.Namespace) -> int:
    from analyzer import DSCAnalyzer

    datadir = _ensure_datadir(args.datadir)
    selected_files = _list_files(datadir, "*.txt")
    if not selected_files:
        raise CliError(f"No input files matching *.txt were found in {datadir}")
    setting_name = args.setting or DEFAULT_DSC_SETTING_NAME
    setting = _clean_setting("dsc", _settings_manager("dsc").load_setting(setting_name))

    analyzer = DSCAnalyzer(
        datadir=datadir,
        save_seg_mode=args.save_segment_data,
        draw_seg_mode=args.draw_segment_plots,
        draw_cycle=args.draw_cycle,
        display_pic=False,
        save_cycle_pic=args.save_cycle_image,
        peaks_upward=args.peaks_upward,
        center_peak=args.center_peak,
        left_length=args.left_length,
        right_length=args.right_length,
        setting_name=setting_name,
        curve_color=_resolve_setting_value(args, "curve_color", setting, "curve_color", DEFAULT_BAR_COLOR),
        line_width=_resolve_setting_value(args, "line_width", setting, "line_width", 1.0),
        axis_width=_resolve_setting_value(args, "axis_width", setting, "axis_width", 1.0),
        title_font_size=_resolve_setting_value(args, "title_font_size", setting, "title_font_size", 20),
        axis_font_size=_resolve_setting_value(args, "axis_font_size", setting, "axis_font_size", 14),
        transparent_back=_resolve_setting_value(args, "transparent_back", setting, "transparent_back", DEFAULT_TRANSPARENT_BACK),
        progress_callback=_progress_callback(args),
    )

    success = analyzer.run()
    if not success:
        raise CliError("DSC analysis failed")

    _emit_result(args, {
        "success": True,
        "message": "DSC analysis complete",
        "cycle_dir": analyzer.cycle_dir,
        "pic_dir": analyzer.pic_dir,
        "files": selected_files,
    })
    return EXIT_OK


def _run_clean(args: argparse.Namespace) -> int:
    datadir = _ensure_datadir(args.datadir)
    if not args.yes:
        raise CliError("Refusing to clean output directories without --yes", EXIT_ARGUMENT_ERROR)

    base = os.path.dirname(datadir)
    output_dirs = [
        os.path.join(base, "Mw_output"),
        os.path.join(base, "GPC_output"),
        os.path.join(base, "DSC_Cycle"),
        os.path.join(base, "DSC_Pic"),
    ]
    cleaned: list[str] = []
    for path in output_dirs:
        if os.path.isdir(path):
            shutil.rmtree(path)
            os.makedirs(path, exist_ok=True)
            cleaned.append(path)

    _emit_result(args, {
        "success": True,
        "message": "Output directories cleaned",
        "cleaned": cleaned,
    })
    return EXIT_OK


def _settings_list(args: argparse.Namespace) -> int:
    manager = _settings_manager(args.type)
    default_name, _default_content = _default_settings(args.type)
    manager.load_setting(default_name)
    settings = manager.list_settings()
    if args.json:
        print(json.dumps({"success": True, "settings": settings}, ensure_ascii=False, indent=2))
    else:
        for name in settings:
            print(name)
    return EXIT_OK


def _settings_show(args: argparse.Namespace) -> int:
    manager = _settings_manager(args.type)
    setting = _clean_setting(args.type, manager.load_setting(args.name))
    if args.json:
        print(json.dumps({"success": True, "setting": setting}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(setting, ensure_ascii=False, indent=2))
    return EXIT_OK


def _settings_save(args: argparse.Namespace) -> int:
    manager = _settings_manager(args.type)
    if args.from_json:
        setting = _read_json_file(args.from_json)
    else:
        setting = _clean_setting(args.type, manager.load_setting(args.base))

    setting.update(_parse_set_items(args.set_items))
    setting = _clean_setting(args.type, setting)
    manager.save_setting(setting, args.name)

    if args.json:
        print(json.dumps({"success": True, "name": args.name, "setting": setting}, ensure_ascii=False, indent=2))
    else:
        print(f"Saved setting: {args.name}")
    return EXIT_OK


def _settings_delete(args: argparse.Namespace) -> int:
    manager = _settings_manager(args.type)
    manager.delete_setting(args.name)
    if args.json:
        print(json.dumps({"success": True, "name": args.name}, ensure_ascii=False, indent=2))
    else:
        print(f"Deleted setting: {args.name}")
    return EXIT_OK


def _add_common_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON to stdout.")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output.")


def _add_file_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--file",
        dest="files",
        nargs="+",
        action="append",
        metavar="NAME",
        help="Input file name(s) inside --datadir. Can be repeated.",
    )


def _add_style_args(parser: argparse.ArgumentParser, *, include_bar: bool) -> None:
    if include_bar:
        parser.add_argument("--bar-color", help="Bar color, e.g. #002FA7.")
        parser.add_argument("--mw-color", help="Mw curve color, e.g. #FF6A07.")
        parser.add_argument("--bar-width", type=float, help="Bar width multiplier.")

        bar_group = parser.add_mutually_exclusive_group()
        bar_group.add_argument("--draw-bar", dest="draw_bar", action="store_true", default=None, help="Draw bars.")
        bar_group.add_argument("--no-bar", dest="draw_bar", action="store_false", help="Do not draw bars.")

        mw_group = parser.add_mutually_exclusive_group()
        mw_group.add_argument("--draw-mw-curve", dest="draw_mw", action="store_true", default=None, help="Draw Mw curve.")
        mw_group.add_argument("--no-mw-curve", dest="draw_mw", action="store_false", help="Do not draw Mw curve.")

        table_group = parser.add_mutually_exclusive_group()
        table_group.add_argument("--draw-table", dest="draw_table", action="store_true", default=None, help="Draw data table.")
        table_group.add_argument("--no-table", dest="draw_table", action="store_false", help="Do not draw data table.")
    else:
        parser.add_argument("--curve-color", help="Curve color, e.g. #002FA7.")

    parser.add_argument("--line-width", type=float, help="Curve line width.")
    parser.add_argument("--axis-width", type=float, help="Axis line width.")
    parser.add_argument("--title-font-size", type=float, help="Title font size.")
    parser.add_argument("--axis-font-size", type=float, help="Axis label font size.")
    bg = parser.add_mutually_exclusive_group()
    bg.add_argument("--transparent-background", dest="transparent_back", action="store_true", default=None)
    bg.add_argument("--opaque-background", dest="transparent_back", action="store_false")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="poly",
        description="PolyAnalyzer batch analysis CLI.",
    )
    parser.add_argument("--version", action="version", version=f"poly {APP_VERSION}")

    subparsers = parser.add_subparsers(dest="command")

    gpc = subparsers.add_parser("gpc", help="Run GPC analysis for .rst files.")
    _add_common_output_args(gpc)
    gpc.add_argument("--datadir", required=True, help="Directory containing input .rst files.")
    gpc.add_argument("--output-name", required=True, help="Output file name without extension.")
    _add_file_args(gpc)
    gpc.add_argument("--overwrite", action="store_true", help="Allow replacing existing output files.")
    gpc.add_argument("--no-csv", dest="save_csv", action="store_false", default=True, help="Do not write GPC CSV summary.")
    gpc.add_argument("--no-image", dest="save_image", action="store_false", default=True, help="Do not write PNG image.")
    gpc.add_argument("--no-xlsx", dest="save_xlsx", action="store_false", default=True, help="Do not write XLSX plot data.")
    gpc.set_defaults(func=_run_gpc)

    mw = subparsers.add_parser("mw", help="Run molecular-weight distribution analysis for .rst files.")
    _add_common_output_args(mw)
    mw.add_argument("--datadir", required=True, help="Directory containing input .rst files.")
    _add_file_args(mw)
    mw.add_argument("--setting", help="Setting file name to load before applying CLI overrides.")
    segment_group = mw.add_mutually_exclusive_group()
    segment_group.add_argument("--segments", type=_parse_segments, help="Comma-separated molecular-weight segment positions.")
    segment_group.add_argument("--ranges", type=_parse_ranges, help="Continuous ranges such as 0-5000,5000-10000.")
    mw.add_argument("--no-image", dest="save_image", action="store_false", default=True, help="Do not write PNG image.")
    _add_style_args(mw, include_bar=True)
    mw.set_defaults(func=_run_mw)

    dsc = subparsers.add_parser("dsc", help="Run DSC analysis for .txt files.")
    _add_common_output_args(dsc)
    dsc.add_argument("--datadir", required=True, help="Directory containing input .txt files.")
    dsc.add_argument("--setting", help="Setting file name to load before applying CLI overrides.")
    dsc.add_argument("--peaks-upward", action="store_true", help="Orient peaks upward.")
    dsc.add_argument("--center-peak", action="store_true", help="Center plots around detected peaks.")
    dsc.add_argument("--left-length", type=float, default=1.9, help="Left trim length for each cycle.")
    dsc.add_argument("--right-length", type=float, default=1.9, help="Right trim length for each cycle.")
    dsc.add_argument("--no-segment-data", dest="save_segment_data", action="store_false", default=True)
    dsc.add_argument("--no-segment-plots", dest="draw_segment_plots", action="store_false", default=True)
    dsc.add_argument("--no-cycle", dest="draw_cycle", action="store_false", default=True)
    dsc.add_argument("--no-cycle-image", dest="save_cycle_image", action="store_false", default=True)
    _add_style_args(dsc, include_bar=False)
    dsc.set_defaults(func=_run_dsc)

    clean = subparsers.add_parser("clean", help="Clean known output directories next to --datadir.")
    _add_common_output_args(clean)
    clean.add_argument("--datadir", required=True, help="Data directory whose sibling output folders should be cleaned.")
    clean.add_argument("--yes", action="store_true", help="Confirm output directory cleanup.")
    clean.set_defaults(func=_run_clean)

    settings = subparsers.add_parser("settings", help="Manage MW/DSC plot settings.")
    settings_subparsers = settings.add_subparsers(dest="settings_command")

    settings_list = settings_subparsers.add_parser("list", help="List settings.")
    _add_common_output_args(settings_list)
    settings_list.add_argument("--type", choices=["mw", "dsc"], default="mw")
    settings_list.set_defaults(func=_settings_list)

    settings_show = settings_subparsers.add_parser("show", help="Show a setting as JSON.")
    _add_common_output_args(settings_show)
    settings_show.add_argument("--type", choices=["mw", "dsc"], default="mw")
    settings_show.add_argument("--name", help="Setting file name. Defaults to the analyzer default.")
    settings_show.set_defaults(func=_settings_show)

    settings_save = settings_subparsers.add_parser("save", help="Save a setting.")
    _add_common_output_args(settings_save)
    settings_save.add_argument("--type", choices=["mw", "dsc"], default="mw")
    settings_save.add_argument("--name", required=True, help="Setting file name to save.")
    settings_save.add_argument("--base", help="Existing setting to load before applying --set.")
    settings_save.add_argument("--from-json", help="Read setting object from a JSON file.")
    settings_save.add_argument("--set", dest="set_items", action="append", metavar="KEY=VALUE", help="Override a setting key. Can be repeated.")
    settings_save.set_defaults(func=_settings_save)

    settings_delete = settings_subparsers.add_parser("delete", help="Delete a setting.")
    _add_common_output_args(settings_delete)
    settings_delete.add_argument("--type", choices=["mw", "dsc"], default="mw")
    settings_delete.add_argument("--name", required=True, help="Setting file name to delete.")
    settings_delete.set_defaults(func=_settings_delete)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help(sys.stderr)
        return EXIT_ARGUMENT_ERROR

    try:
        return args.func(args)
    except CliError as exc:
        if getattr(args, "json", False):
            print(json.dumps({"success": False, "error": exc.message}, ensure_ascii=False, indent=2))
        else:
            print(f"Error: {exc.message}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return EXIT_ANALYSIS_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
