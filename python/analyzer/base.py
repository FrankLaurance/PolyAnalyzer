"""
PolyAnalyzer base module — constants, logging, validation, settings, and base analyzer.

Extracted from the monolithic main.py for the v2 refactoring.
All streamlit dependencies have been removed; UI feedback is handled via callbacks.
"""

import os
import glob
import json
import logging
import platform
import subprocess
import numpy as np
from datetime import datetime
from typing import List, Optional, Tuple, Callable, Any, Dict

from numpy.typing import NDArray

import sys


def get_install_dir() -> str:
    """Get the installation directory (exe dir for packaged, project root for dev)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        # base.py -> analyzer/ -> python/ -> project_root/
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Matplotlib backend (non-interactive)
# ---------------------------------------------------------------------------
os.environ["MPLBACKEND"] = "Agg"

# ---------------------------------------------------------------------------
# Constants — default settings
# ---------------------------------------------------------------------------
APP_VERSION: str = "1.1.2"
DEFAULT_BAR_COLOR: str = "#002FA7"
DEFAULT_MW_COLOR: str = "#FF6A07"
DEFAULT_SETTING_NAME: str = "defaultSetting.ini"
DEFAULT_DSC_SETTING_NAME: str = "defaultDSCSetting.ini"
DEFAULT_TRANSPARENT_BACK: bool = True

# ---------------------------------------------------------------------------
# Constants — figure parameters
# ---------------------------------------------------------------------------
FIGURE_DPI: int = 300
FIGURE_SIZE_WITH_TABLE: Tuple[int, int] = (12, 8)
FIGURE_SIZE_WITHOUT_TABLE: Tuple[float, int] = (7.5, 8)
GPC_FIGURE_SIZE: Tuple[int, int] = (16, 8)
GRIDSPEC_ROWS: int = 8
GRIDSPEC_COLS: int = 8

# ---------------------------------------------------------------------------
# Constants — data processing
# ---------------------------------------------------------------------------
MW_DATA_OFFSET: int = 3          # MW数据起始偏移量
NORM_COLUMN_INDEX: int = 2       # 归一化数据列索引
MW_COLUMN_INDEX: int = 4         # 分子量数据列索引
GPC_X_COLUMN_INDEX: int = 5      # GPC X轴数据列索引
GPC_Y_COLUMN_INDEX: int = 6      # GPC Y轴数据列索引
MIN_PEAK_COLUMNS: int = 4        # 峰数据最小列数
MIN_GPC_PEAK_COLUMNS: int = 6    # GPC峰数据最小列数
MIN_MW_DATA_COLUMNS: int = 8     # 分子量数据最小列数

# ---------------------------------------------------------------------------
# Constants — calculation parameters
# ---------------------------------------------------------------------------
NORM_SCALE_FACTOR: int = 50              # 归一化缩放因子
PERCENTAGE_FACTOR: int = 100             # 百分比转换因子
BAR_POSITION_WEIGHT_LEFT: float = 0.75   # 柱状图位置左权重
BAR_POSITION_WEIGHT_RIGHT: float = 0.25  # 柱状图位置右权重


# ===================================================================
# Logger
# ===================================================================

class Logger:
    """日志管理器 - 提供结构化日志记录功能

    All ``show_ui`` parameters are retained for API compatibility but no
    longer trigger any UI side-effects.  A *warning_callback* /
    *error_callback* / *success_callback* can optionally be supplied to
    forward messages to an external UI layer.
    """

    def __init__(
        self,
        name: str = "PolyAnalyzer",
        level: int = logging.INFO,
        warning_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        success_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self._warning_cb = warning_callback
        self._error_cb = error_callback
        self._success_cb = success_callback

        # 避免重复添加处理器
        if not self.logger.handlers:
            log_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(log_dir, exist_ok=True)

            log_file = os.path.join(
                log_dir, f"gpc_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)

            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    # -- public API --------------------------------------------------------

    def debug(self, message: str) -> None:
        """调试信息"""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """一般信息"""
        self.logger.info(message)

    def warning(self, message: str, show_ui: bool = True) -> None:
        """警告信息"""
        self.logger.warning(message)
        if show_ui and self._warning_cb:
            self._warning_cb(message)

    def error(
        self,
        message: str,
        show_ui: bool = True,
        exception: Optional[Exception] = None,
    ) -> None:
        """错误信息"""
        if exception:
            self.logger.error(f"{message}: {str(exception)}", exc_info=True)
        else:
            self.logger.error(message)
        if show_ui and self._error_cb:
            self._error_cb(message)

    def success(self, message: str, show_ui: bool = True) -> None:
        """成功信息"""
        self.logger.info(f"SUCCESS: {message}")
        if show_ui and self._success_cb:
            self._success_cb(message)


# ===================================================================
# DataValidator
# ===================================================================

class DataValidator:
    """数据验证器 - 集中管理数据验证逻辑"""

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger: Logger = logger or Logger()

    def validate_file_exists(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            self.logger.error(f"文件未找到: {file_path}")
            return False
        return True

    def validate_data_lines(self, lines: List[str]) -> bool:
        if not lines:
            self.logger.error("数据文件为空，无法处理")
            return False
        return True

    def validate_markers(self, mw_start: int, mw_end: int, slice_table_start: int) -> bool:
        if mw_start == 0 or mw_end == 0 or slice_table_start == 0:
            self.logger.error("数据文件格式错误：缺少必要的标记")
            return False
        if mw_end <= mw_start + MW_DATA_OFFSET:
            self.logger.error("数据文件格式错误：分子量数据区域无效")
            return False
        return True

    def validate_array_shape(
        self,
        array: NDArray[np.float64],
        min_rows: int = 0,
        min_cols: int = 0,
        name: str = "数组",
    ) -> bool:
        if array.shape[0] < min_rows:
            self.logger.warning(f"{name}行数不足: {array.shape[0]} < {min_rows}")
            return False
        if array.shape[1] < min_cols:
            self.logger.warning(f"{name}列数不足: {array.shape[1]} < {min_cols}")
            return False
        return True

    def validate_data_not_empty(self, data: Any, name: str = "数据") -> bool:
        if data is None or (hasattr(data, "__len__") and len(data) == 0):
            self.logger.error(f"未找到{name}")
            return False
        return True

    def validate_segment_positions(self, positions: List[int]) -> bool:
        if len(positions) < 2:
            self.logger.error("至少需要2个分割位置")
            return False
        return True


# ===================================================================
# Global logger instance
# ===================================================================
logger = Logger()


# ===================================================================
# SettingsManager
# ===================================================================

class SettingsManager:
    """设置管理器 - 负责读取、保存和管理绘图设置"""

    def __init__(
        self,
        setting_dir: str,
        setting_name: str,
        default_content: Dict[str, Any],
    ) -> None:
        self.setting_dir = setting_dir
        self.setting_name = setting_name
        self.default_content = default_content
        self._ensure_setting_dir()

    def _ensure_setting_dir(self) -> None:
        if not os.path.exists(self.setting_dir):
            os.makedirs(self.setting_dir, exist_ok=True)

    def get_setting_path(self, name: Optional[str] = None) -> str:
        filename = name if name else self.setting_name
        return os.path.join(self.setting_dir, filename)

    def list_settings(self) -> List[str]:
        return [
            os.path.basename(i)
            for i in glob.glob(os.path.join(self.setting_dir, "*.ini"))
        ]

    def load_setting(self, setting_name: Optional[str] = None) -> Dict[str, Any]:
        name = setting_name if setting_name else self.setting_name
        setting_path = self.get_setting_path(name)

        if not os.path.exists(setting_path):
            return self.create_default_setting()

        try:
            with open(setting_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                try:
                    setting = json.loads(content)
                except json.JSONDecodeError:
                    import ast
                    setting = ast.literal_eval(content)
            return self._normalize_setting_keys(setting)
        except Exception as e:
            logger.warning(f"读取设置文件失败: {e}，使用默认设置")
            return self.create_default_setting()

    def _normalize_setting_keys(self, setting: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        key_mappings: Dict[str, List[str]] = {
            "bar_color": ["barColor"],
            "mw_color": ["MwColor"],
            "bar_width": ["barWidth"],
            "line_width": ["lineWidth"],
            "axis_width": ["axisWidth"],
            "title_font_size": ["titleFontSize"],
            "axis_font_size": ["axisFontSize"],
            "draw_bar": ["drawBar"],
            "draw_mw": ["drawMw"],
            "draw_table": ["drawTable"],
            "transparent_back": ["transparentBack"],
            "segmentpos": [],
            "curve_color": [],
        }

        for new_key, old_keys in key_mappings.items():
            if new_key in setting:
                normalized[new_key] = setting[new_key]
            else:
                for old_key in old_keys:
                    if old_key in setting:
                        normalized[new_key] = setting[old_key]
                        break
                else:
                    normalized[new_key] = self._get_default_value(new_key)

        return normalized

    def _get_default_value(self, key: str) -> Any:
        return self.default_content.get(key)

    def create_default_setting(self) -> Dict[str, Any]:
        self.save_setting(self.default_content, self.setting_name)
        return self.default_content

    def save_setting(self, setting: Dict[str, Any], name: Optional[str] = None) -> None:
        filename = name if name else self.setting_name
        setting_path = self.get_setting_path(filename)
        try:
            with open(setting_path, "w", encoding="utf-8") as f:
                json.dump(setting, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存设置失败: {e}")

    def delete_setting(self, setting_name: str) -> None:
        setting_path = self.get_setting_path(setting_name)
        try:
            os.remove(setting_path)
            if len(os.listdir(self.setting_dir)) == 0:
                self.create_default_setting()
        except Exception as e:
            logger.error(f"删除设置失败: {e}")


# ===================================================================
# BaseAnalyzer
# ===================================================================

class BaseAnalyzer:
    """分析器基类 — 文件/目录操作、设置管理、进度回调等公共功能。

    Sub-classes (``GPCAnalyzer``, ``MolecularWeightAnalyzer``,
    ``DSCAnalyzer``) inherit from this class.
    """

    def __init__(
        self,
        datadir: str,
        test_mode: bool = False,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        info_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.rootdir: str = os.path.dirname(os.path.abspath(__file__))
        if datadir:
            self.data_path: str = os.path.abspath(datadir)
        else:
            self.data_path: str = os.path.join(self.rootdir, "datapath")
        self._cached_file_list: Optional[List[str]] = None
        self.lines: List[str] = []
        self.filename: str = ""
        self.sample_name: str = ""
        self.mw_data: list = []
        self.peak_num: int = 0
        self.peak_pos: list = []
        self.peak_data: dict = {}

        # 运行模式
        self.test_mode: bool = test_mode

        # 回调
        self.progress_callback = progress_callback
        self.info_callback = info_callback

        # 集成日志器和验证器
        self.logger: Logger = logger
        self.validator: DataValidator = DataValidator(self.logger)

    # -- folder operations -------------------------------------------------

    def open_folder(self, path: str) -> None:
        """跨平台打开文件夹"""
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", path])
            else:
                self.logger.warning("不支持的操作系统")
        except Exception as e:
            self.logger.error(f"无法打开文件夹: {e}")

    # -- reset / clear -----------------------------------------------------

    def reset(self, reset_peak_data: bool = True) -> None:
        """重置所有数据属性"""
        self.lines = []
        self.filename = ""
        self.sample_name = ""
        self.mw_data = []
        self.peak_num = 0
        self.peak_pos = []
        if reset_peak_data:
            self.peak_data = {}

    def clear_dir(self, output_dir: str) -> None:
        """清空输出目录"""
        if not os.path.exists(output_dir):
            return
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                self.logger.warning(f"删除文件失败 {filename}: {e}")

    # -- file I/O ----------------------------------------------------------

    def read_file(self, name: str, reset_peak_data: bool = True) -> bool:
        """读取数据文件（ASCII 编码，过滤空行）"""
        self.reset(reset_peak_data=reset_peak_data)
        self.filename = name
        file_path = os.path.join(self.data_path, name)

        try:
            with open(file_path, "r", encoding="ascii") as file:
                self.lines = [line.strip() for line in file if line.strip()]
            return True
        except FileNotFoundError:
            self.logger.error(f"文件未找到: {name}", show_ui=True)
            return False
        except UnicodeDecodeError:
            self.logger.error(
                f"文件编码错误: {name}，请确保文件为ASCII编码", show_ui=True
            )
            return False
        except Exception as e:
            self.logger.error(f"读取文件失败 {name}", show_ui=True, exception=e)
            return False

    def read_file_list(self, force_refresh: bool = False) -> List[str]:
        """读取数据目录中的所有 .rst 文件列表（带缓存）"""
        if self._cached_file_list is None or force_refresh:
            self._cached_file_list = [
                os.path.basename(i)
                for i in glob.glob(os.path.join(self.data_path, "*.rst"))
            ]
        return self._cached_file_list

    def check_dir(self) -> bool:
        """检查输出目录中是否存在同名文件（子类应覆盖）"""
        return False

    # -- settings (delegates to SettingsManager) ---------------------------

    def load_setting(self, setting_name: Optional[str] = None) -> Dict[str, Any]:
        """读取设置文件（需要子类先初始化 ``self.settings_manager``）"""
        return self.settings_manager.load_setting(setting_name)

    def save_setting(self, new_setting_name: str = "") -> None:
        """保存当前设置（子类应覆盖以构造 setting dict）"""
        raise NotImplementedError

    def delete_setting(self, settingname: str) -> None:
        """删除指定的设置文件"""
        self.settings_manager.delete_setting(settingname)

    def change_setting(self, settingname: str) -> None:
        """切换到指定的设置（子类可覆盖）"""
        self.setting_name = settingname

    def setting_list(self) -> List[str]:
        """获取所有设置文件列表"""
        return self.settings_manager.list_settings()

    # -- preprocessing -----------------------------------------------------

    def preprocess_common(self) -> Tuple[int, int, int]:
        """预处理数据的公共部分，提取关键位置

        Returns:
            (mw_start, mw_end, slice_table_start)
        """
        mw_start = 0
        mw_end = 0
        slice_table_start = 0

        if not self.validator.validate_data_lines(self.lines):
            raise ValueError("数据文件为空，无法处理")

        for pos, line in enumerate(self.lines):
            if "Sample Name" in line:
                parts = line.split("\t")
                if len(parts) > 1:
                    self.sample_name = parts[1]
            elif "<MW_Averages>" in line:
                mw_start = pos
            elif "</MW_Averages>" in line:
                mw_end = pos
            elif "<Slice_Table>" in line:
                slice_table_start = pos
                break

        if not self.validator.validate_markers(mw_start, mw_end, slice_table_start):
            raise ValueError("数据文件格式错误")

        return mw_start, mw_end, slice_table_start
