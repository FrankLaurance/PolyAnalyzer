"""JSON-RPC 2.0 server over stdin/stdout for PolyAnalyzer."""

from __future__ import annotations

import glob
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import traceback
from typing import Any, Callable

from analyzer import (
    GPCAnalyzer,
    MolecularWeightAnalyzer,
    DSCAnalyzer,
    SettingsManager,
    DEFAULT_SETTING_NAME,
    DEFAULT_DSC_SETTING_NAME,
    DEFAULT_BAR_COLOR,
    DEFAULT_MW_COLOR,
    DEFAULT_TRANSPARENT_BACK,
)

logger = logging.getLogger(__name__)

# JSON-RPC 2.0 error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

MethodHandler = Callable[[dict[str, Any]], Any]

# Root directory for analyzers (same as BaseAnalyzer.rootdir)
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class JsonRpcError(Exception):
    """JSON-RPC error with code and optional data."""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        err: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            err["data"] = self.data
        return err


def _write_response(response: dict[str, Any]) -> None:
    """Write a JSON-RPC response to stdout."""
    line = json.dumps(response, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def send_notification(method: str, params: dict[str, Any] | None = None) -> None:
    """Send a JSON-RPC notification (no id) for progress updates."""
    msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    _write_response(msg)


def _make_progress_callback() -> Callable[[float, str], None]:
    """Create a progress callback that emits JSON-RPC notifications."""

    def callback(progress: float, message: str) -> None:
        send_notification("progress", {"progress": progress, "message": message})

    return callback


def _require_param(params: dict[str, Any], key: str, label: str | None = None) -> Any:
    """Extract a required parameter or raise INVALID_PARAMS."""
    if key not in params:
        raise JsonRpcError(INVALID_PARAMS, f"Missing required parameter: {label or key}")
    return params[key]


# ---------------------------------------------------------------------------
# GPC handlers
# ---------------------------------------------------------------------------

def _gpc_analyze(params: dict[str, Any]) -> Any:
    output_filename = _require_param(params, "output_filename")
    selected_files: list[str] | None = params.get("selected_files")
    datadir = params.get("datadir", "")

    analyzer = GPCAnalyzer(
        datadir=datadir,
        output_filename=output_filename,
        save_file=params.get("save_file", True),
        save_picture=params.get("save_picture", True),
        display_mode=params.get("display_mode", True),
        save_figure_file_gpc=params.get("save_figure_file_gpc", True),
        progress_callback=_make_progress_callback(),
    )
    if selected_files is not None:
        analyzer.selected_file = selected_files

    success = analyzer.run()
    if not success:
        raise JsonRpcError(INTERNAL_ERROR, "GPC analysis failed")
    return {"success": True, "output_dir": analyzer.output_dir}


def _gpc_list_files(params: dict[str, Any]) -> Any:
    datadir = params.get("datadir", "")
    analyzer = GPCAnalyzer(datadir=datadir, output_filename="")
    files = analyzer.read_file_list(force_refresh=params.get("force_refresh", False))
    return {"files": files}


def _gpc_check_output(params: dict[str, Any]) -> Any:
    output_filename = _require_param(params, "output_filename")
    datadir = params.get("datadir", "")
    analyzer = GPCAnalyzer(datadir=datadir, output_filename=output_filename)
    return {"exists": analyzer.check_dir()}


# ---------------------------------------------------------------------------
# MW handlers
# ---------------------------------------------------------------------------

def _mw_analyze(params: dict[str, Any]) -> Any:
    selected_files: list[str] | None = params.get("selected_files")
    if not selected_files:
        raise JsonRpcError(INVALID_PARAMS, "selected_files is required and must not be empty")
    datadir = params.get("datadir", "")

    analyzer = MolecularWeightAnalyzer(
        datadir=datadir,
        save_file=params.get("save_file", True),
        save_picture=params.get("save_picture", True),
        display_picture=params.get("display_picture", False),
        bar_color=params.get("bar_color", DEFAULT_BAR_COLOR),
        mw_color=params.get("mw_color", DEFAULT_MW_COLOR),
        bar_width=params.get("bar_width", 1.2),
        line_width=params.get("line_width", 1.0),
        axis_width=params.get("axis_width", 1.0),
        title_font_size=params.get("title_font_size", 20),
        axis_font_size=params.get("axis_font_size", 14),
        transparent_back=params.get("transparent_back", DEFAULT_TRANSPARENT_BACK),
        draw_bar=params.get("draw_bar", True),
        draw_mw=params.get("draw_mw", True),
        draw_table=params.get("draw_table", True),
        setting_name=params.get("setting_name", DEFAULT_SETTING_NAME),
        progress_callback=_make_progress_callback(),
    )
    analyzer.selected_file = selected_files

    if "segmentpos" in params:
        analyzer.segmentpos = sorted(params["segmentpos"])
        analyzer.selectedpos = list(analyzer.segmentpos)
        analyzer.segmentnum = len(analyzer.segmentpos)

    success = analyzer.run()
    if not success:
        raise JsonRpcError(INTERNAL_ERROR, "MW analysis failed")
    return {"success": True, "output_dir": analyzer.output_dir}


def _mw_list_files(params: dict[str, Any]) -> Any:
    datadir = params.get("datadir", "")
    analyzer = MolecularWeightAnalyzer(datadir=datadir)
    files = analyzer.read_file_list(force_refresh=params.get("force_refresh", False))
    return {"files": files}


def _mw_get_segments(params: dict[str, Any]) -> Any:
    datadir = params.get("datadir", "")
    setting_name = params.get("setting_name", DEFAULT_SETTING_NAME)
    analyzer = MolecularWeightAnalyzer(datadir=datadir, setting_name=setting_name)
    return {"segments": analyzer.segmentpos}


def _mw_add_segment(params: dict[str, Any]) -> Any:
    position = _require_param(params, "position")
    if not isinstance(position, (int, float)):
        raise JsonRpcError(INVALID_PARAMS, "position must be a number")
    datadir = params.get("datadir", "")
    setting_name = params.get("setting_name", DEFAULT_SETTING_NAME)

    analyzer = MolecularWeightAnalyzer(datadir=datadir, setting_name=setting_name)
    analyzer.add_region(int(position))
    analyzer.selectedpos = list(analyzer.segmentpos)
    analyzer.segmentnum = len(analyzer.segmentpos)
    return {"segments": analyzer.segmentpos}


def _mw_check_output(params: dict[str, Any]) -> Any:
    selected_files = params.get("selected_files")
    datadir = params.get("datadir", "")
    analyzer = MolecularWeightAnalyzer(datadir=datadir)
    if selected_files is not None:
        analyzer.selected_file = selected_files
    return {"exists": analyzer.check_dir()}


# ---------------------------------------------------------------------------
# DSC handlers
# ---------------------------------------------------------------------------

def _dsc_analyze(params: dict[str, Any]) -> Any:
    datadir = params.get("datadir", "")
    if not datadir:
        raise JsonRpcError(INVALID_PARAMS, "datadir is required for DSC analysis")

    analyzer = DSCAnalyzer(
        datadir=datadir,
        save_seg_mode=params.get("save_seg_mode", True),
        draw_seg_mode=params.get("draw_seg_mode", True),
        draw_cycle=params.get("draw_cycle", True),
        display_pic=params.get("display_pic", True),
        save_cycle_pic=params.get("save_cycle_pic", True),
        peaks_upward=params.get("peaks_upward", False),
        center_peak=params.get("center_peak", False),
        left_length=params.get("left_length", 1.9),
        right_length=params.get("right_length", 1.9),
        setting_name=params.get("setting_name", DEFAULT_DSC_SETTING_NAME),
        progress_callback=_make_progress_callback(),
    )

    success = analyzer.run()
    if not success:
        raise JsonRpcError(INTERNAL_ERROR, "DSC analysis failed")
    return {
        "success": True,
        "cycle_dir": analyzer.cycle_dir,
        "pic_dir": analyzer.pic_dir,
    }


def _dsc_list_files(params: dict[str, Any]) -> Any:
    datadir = params.get("datadir", "")
    if not datadir:
        raise JsonRpcError(INVALID_PARAMS, "datadir is required")
    files = [
        os.path.basename(f)
        for f in glob.glob(os.path.join(datadir, "*.txt"))
    ]
    return {"files": files}


# ---------------------------------------------------------------------------
# Settings handlers
# ---------------------------------------------------------------------------

def _get_settings_manager(params: dict[str, Any]) -> SettingsManager:
    """Build a SettingsManager from request params."""
    analyzer_type = params.get("type", "mw")
    setting_dir = os.path.join(_ROOT_DIR, "setting")

    if analyzer_type == "dsc":
        default_name = DEFAULT_DSC_SETTING_NAME
        default_content: dict[str, Any] = {
            "curve_color": DEFAULT_BAR_COLOR,
            "transparent_back": DEFAULT_TRANSPARENT_BACK,
            "line_width": 1.0,
            "axis_width": 1.0,
            "title_font_size": 20,
            "axis_font_size": 14,
        }
    else:
        default_name = DEFAULT_SETTING_NAME
        default_content = {
            "segmentpos": [0, 5000, 10000, 50000, 100000, 500000,
                           1000000, 5000000, 10000000, 50000000],
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

    return SettingsManager(setting_dir, default_name, default_content)


def _settings_load(params: dict[str, Any]) -> Any:
    mgr = _get_settings_manager(params)
    name = params.get("name")
    return {"setting": mgr.load_setting(name)}


def _settings_save(params: dict[str, Any]) -> Any:
    setting_data = _require_param(params, "setting")
    name = params.get("name")
    mgr = _get_settings_manager(params)
    mgr.save_setting(setting_data, name)
    return {"success": True}


def _settings_delete(params: dict[str, Any]) -> Any:
    name = _require_param(params, "name")
    mgr = _get_settings_manager(params)
    mgr.delete_setting(name)
    return {"success": True}


def _settings_list(params: dict[str, Any]) -> Any:
    mgr = _get_settings_manager(params)
    return {"settings": mgr.list_settings()}


# ---------------------------------------------------------------------------
# System handlers
# ---------------------------------------------------------------------------

def _system_open_folder(params: dict[str, Any]) -> Any:
    path = _require_param(params, "path")
    if not os.path.isdir(path):
        raise JsonRpcError(INVALID_PARAMS, f"Directory does not exist: {path}")

    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(path)  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.run(["open", path], check=True)
        elif system == "Linux":
            subprocess.run(["xdg-open", path], check=True)
        else:
            raise JsonRpcError(INTERNAL_ERROR, f"Unsupported platform: {system}")
    except JsonRpcError:
        raise
    except Exception as e:
        raise JsonRpcError(INTERNAL_ERROR, f"Failed to open folder: {e}")
    return {"success": True}


def _system_clean_output(params: dict[str, Any]) -> Any:
    datadir = params.get("datadir", "")
    if datadir:
        base = os.path.dirname(datadir)
    else:
        base = os.path.dirname(_ROOT_DIR)
    output_dirs = [
        os.path.join(base, "Mw_output"),
        os.path.join(base, "GPC_output"),
        os.path.join(base, "DSC_Cycle"),
        os.path.join(base, "DSC_Pic"),
    ]
    cleaned: list[str] = []
    for dir_path in output_dirs:
        if os.path.isdir(dir_path):
            shutil.rmtree(dir_path, ignore_errors=True)
            os.makedirs(dir_path, exist_ok=True)
            cleaned.append(dir_path)
    return {"success": True, "cleaned": cleaned}


def _system_get_default_datapath(params: dict[str, Any]) -> Any:
    """Return the default datapath (project_root/datapath)."""
    project_root = os.path.dirname(_ROOT_DIR)
    datapath = os.path.join(project_root, "datapath")
    return {"datapath": datapath}


# ---------------------------------------------------------------------------
# Method registry
# ---------------------------------------------------------------------------

METHOD_TABLE: dict[str, MethodHandler] = {
    "gpc.analyze": _gpc_analyze,
    "gpc.list_files": _gpc_list_files,
    "gpc.check_output": _gpc_check_output,
    "mw.analyze": _mw_analyze,
    "mw.list_files": _mw_list_files,
    "mw.get_segments": _mw_get_segments,
    "mw.add_segment": _mw_add_segment,
    "mw.check_output": _mw_check_output,
    "dsc.analyze": _dsc_analyze,
    "dsc.list_files": _dsc_list_files,
    "settings.load": _settings_load,
    "settings.save": _settings_save,
    "settings.delete": _settings_delete,
    "settings.list": _settings_list,
    "system.open_folder": _system_open_folder,
    "system.clean_output": _system_clean_output,
    "system.get_default_datapath": _system_get_default_datapath,
}


# ---------------------------------------------------------------------------
# Request handling
# ---------------------------------------------------------------------------

def _make_error_response(
    req_id: int | str | None,
    code: int,
    message: str,
    data: Any = None,
) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "error": err, "id": req_id}


def _make_success_response(req_id: int | str | None, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "result": result, "id": req_id}


def _handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    """Process a single JSON-RPC request. Returns None for notifications."""
    if request.get("jsonrpc") != "2.0":
        return _make_error_response(
            request.get("id"), INVALID_REQUEST, "Invalid JSON-RPC version"
        )

    method = request.get("method")
    if not isinstance(method, str):
        return _make_error_response(
            request.get("id"), INVALID_REQUEST, "Missing or invalid 'method'"
        )

    params: dict[str, Any] = request.get("params", {})
    if not isinstance(params, dict):
        return _make_error_response(
            request.get("id"), INVALID_PARAMS, "Params must be an object"
        )

    req_id = request.get("id")
    is_notification = "id" not in request

    handler = METHOD_TABLE.get(method)
    if handler is None:
        if is_notification:
            return None
        return _make_error_response(req_id, METHOD_NOT_FOUND, f"Method not found: {method}")

    try:
        result = handler(params)
    except JsonRpcError as exc:
        if is_notification:
            return None
        return _make_error_response(req_id, exc.code, exc.message, exc.data)
    except Exception as exc:
        logger.exception("Unhandled error in method %s", method)
        if is_notification:
            return None
        return _make_error_response(
            req_id,
            INTERNAL_ERROR,
            str(exc),
            traceback.format_exc(),
        )

    # Notifications must not produce a response
    if is_notification:
        return None

    return _make_success_response(req_id, result)


def handle_line(line: str) -> None:
    """Parse a single line of JSON-RPC input and write the response."""
    try:
        request = json.loads(line)
    except json.JSONDecodeError as exc:
        _write_response(_make_error_response(None, PARSE_ERROR, str(exc)))
        return

    # Batch requests
    if isinstance(request, list):
        responses: list[dict[str, Any]] = []
        for item in request:
            resp = _handle_request(item)
            if resp is not None:
                responses.append(resp)
        if responses:
            _write_response(responses)  # type: ignore[arg-type]
        return

    resp = _handle_request(request)
    if resp is not None:
        _write_response(resp)


def serve() -> None:
    """Main loop: read JSON-RPC requests from stdin, one per line."""
    logger.info("JSON-RPC server started, reading from stdin")
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            handle_line(line)
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception:
        logger.exception("Fatal error in server loop")
        raise
    finally:
        logger.info("JSON-RPC server stopped")
