import streamlit as st
import os
import time
import numpy as np
# matplotlib 和 plottable 改为延迟加载,减少 PyInstaller 打包体积
# import matplotlib.pyplot as plt
# import matplotlib.gridspec as gridspec
# from plottable import Table, ColumnDefinition
import glob
import pandas as pd
from typing import List, Optional, Tuple, Callable, Any, Dict, Union
import platform
import subprocess
import json
import logging
from datetime import datetime
from numpy.typing import NDArray

# 设置 matplotlib 后端为 Agg (非交互式),减少依赖
os.environ['MPLBACKEND'] = 'Agg'

# 常量定义 - 默认设置
DEFAULT_BAR_COLOR = "#002FA7"
DEFAULT_MW_COLOR = "#FF6A07"
DEFAULT_SETTING_NAME = "defaultSetting.ini"
DEFAULT_TRANSPARENT_BACK = True

# 常量定义 - 图形参数
FIGURE_DPI = 300
FIGURE_SIZE_WITH_TABLE = (12, 8)
FIGURE_SIZE_WITHOUT_TABLE = (7.5, 8)
GPC_FIGURE_SIZE = (16, 8)
GRIDSPEC_ROWS = 8
GRIDSPEC_COLS = 8

# 常量定义 - 数据处理
MW_DATA_OFFSET = 3  # MW数据起始偏移量
NORM_COLUMN_INDEX = 2  # 归一化数据列索引
MW_COLUMN_INDEX = 4  # 分子量数据列索引
GPC_X_COLUMN_INDEX = 5  # GPC X轴数据列索引
GPC_Y_COLUMN_INDEX = 6  # GPC Y轴数据列索引
MIN_PEAK_COLUMNS = 4  # 峰数据最小列数
MIN_GPC_PEAK_COLUMNS = 6  # GPC峰数据最小列数
MIN_MW_DATA_COLUMNS = 8  # 分子量数据最小列数

# 常量定义 - 计算参数
NORM_SCALE_FACTOR = 50  # 归一化缩放因子
PERCENTAGE_FACTOR = 100  # 百分比转换因子
BAR_POSITION_WEIGHT_LEFT = 0.75  # 柱状图位置左权重
BAR_POSITION_WEIGHT_RIGHT = 0.25  # 柱状图位置右权重


class Logger:
    """日志管理器 - 提供结构化日志记录功能"""
    
    def __init__(self, name: str = "GPCtoPic", level: int = logging.INFO):
        """初始化日志器
        
        Args:
            name: 日志器名称
            level: 日志级别
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 创建日志目录
            log_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(log_dir, exist_ok=True)
            
            # 文件处理器
            log_file = os.path.join(log_dir, f"gpc_{datetime.now().strftime('%Y%m%d')}.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # 格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str) -> None:
        """调试信息"""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """一般信息"""
        self.logger.info(message)
    
    def warning(self, message: str, show_ui: bool = True) -> None:
        """警告信息
        
        Args:
            message: 警告消息
            show_ui: 是否在UI中显示
        """
        self.logger.warning(message)
        if show_ui:
            st.warning(message)
    
    def error(self, message: str, show_ui: bool = True, exception: Optional[Exception] = None) -> None:
        """错误信息
        
        Args:
            message: 错误消息
            show_ui: 是否在UI中显示
            exception: 异常对象
        """
        if exception:
            self.logger.error(f"{message}: {str(exception)}", exc_info=True)
        else:
            self.logger.error(message)
        
        if show_ui:
            st.error(message)
    
    def success(self, message: str, show_ui: bool = True) -> None:
        """成功信息
        
        Args:
            message: 成功消息
            show_ui: 是否在UI中显示
        """
        self.logger.info(f"SUCCESS: {message}")
        if show_ui:
            st.success(message)


class DataValidator:
    """数据验证器 - 集中管理数据验证逻辑"""
    
    def __init__(self, logger: Optional[Logger] = None) -> None:
        """初始化验证器
        
        Args:
            logger: 日志器实例
        """
        self.logger: Logger = logger or Logger()
    
    def validate_file_exists(self, file_path: str) -> bool:
        """验证文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 文件存在返回True
        """
        if not os.path.exists(file_path):
            self.logger.error(f"文件未找到: {file_path}")
            return False
        return True
    
    def validate_data_lines(self, lines: List[str]) -> bool:
        """验证数据行是否为空
        
        Args:
            lines: 数据行列表
            
        Returns:
            bool: 数据有效返回True
        """
        if not lines:
            self.logger.error("数据文件为空，无法处理")
            return False
        return True
    
    def validate_markers(self, mw_start: int, mw_end: int, slice_table_start: int) -> bool:
        """验证关键标记是否找到
        
        Args:
            mw_start: MW起始位置
            mw_end: MW结束位置
            slice_table_start: 切片表起始位置
            
        Returns:
            bool: 标记有效返回True
        """
        if mw_start == 0 or mw_end == 0 or slice_table_start == 0:
            self.logger.error("数据文件格式错误：缺少必要的标记")
            return False
        
        if mw_end <= mw_start + MW_DATA_OFFSET:
            self.logger.error("数据文件格式错误：分子量数据区域无效")
            return False
        
        return True
    
    def validate_array_shape(self, array: NDArray[np.float64], min_rows: int = 0, 
                           min_cols: int = 0, name: str = "数组") -> bool:
        """验证数组形状
        
        Args:
            array: numpy数组
            min_rows: 最小行数
            min_cols: 最小列数
            name: 数组名称（用于错误消息）
            
        Returns:
            bool: 形状有效返回True
        """
        if array.shape[0] < min_rows:
            self.logger.warning(f"{name}行数不足: {array.shape[0]} < {min_rows}")
            return False
        
        if array.shape[1] < min_cols:
            self.logger.warning(f"{name}列数不足: {array.shape[1]} < {min_cols}")
            return False
        
        return True
    
    def validate_data_not_empty(self, data: Any, name: str = "数据") -> bool:
        """验证数据不为空
        
        Args:
            data: 要验证的数据
            name: 数据名称
            
        Returns:
            bool: 数据不为空返回True
        """
        if data is None or (hasattr(data, '__len__') and len(data) == 0):
            self.logger.error(f"未找到{name}")
            return False
        return True
    
    def validate_segment_positions(self, positions: List[int]) -> bool:
        """验证分段位置
        
        Args:
            positions: 分段位置列表
            
        Returns:
            bool: 位置有效返回True
        """
        if len(positions) < 2:
            self.logger.error("至少需要2个分割位置")
            return False
        return True


# 创建全局日志器实例
logger = Logger()

def open_folder(path: str) -> None:
    """跨平台打开文件夹
    
    Args:
        path: 文件夹路径
    """
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path])
        elif platform.system() == "Linux":
            subprocess.run(["xdg-open", path])
        else:
            st.warning("不支持的操作系统")
    except Exception as e:
        st.error(f"无法打开文件夹: {e}")


class SettingsManager:
    """设置管理器 - 负责读取、保存和管理绘图设置"""
    
    def __init__(self, setting_dir: str, setting_name: str = DEFAULT_SETTING_NAME):
        """初始化设置管理器
        
        Args:
            setting_dir: 设置文件目录
            setting_name: 设置文件名
        """
        self.setting_dir = setting_dir
        self.setting_name = setting_name
        self._ensure_setting_dir()
    
    def _ensure_setting_dir(self) -> None:
        """确保设置目录存在"""
        if not os.path.exists(self.setting_dir):
            os.makedirs(self.setting_dir, exist_ok=True)
    
    def get_setting_path(self, name: str = None) -> str:
        """获取设置文件完整路径
        
        Args:
            name: 设置文件名，如果为None则使用默认名称
            
        Returns:
            设置文件完整路径
        """
        filename = name if name else self.setting_name
        return os.path.join(self.setting_dir, filename)
    
    def list_settings(self) -> List[str]:
        """获取所有设置文件列表
        
        Returns:
            设置文件名列表
        """
        return [os.path.basename(i) for i in glob.glob(os.path.join(self.setting_dir, "*.ini"))]
    
    def load_setting(self, setting_name: Optional[str] = None) -> Dict[str, Any]:
        """读取设置文件
        
        Args:
            setting_name: 设置文件名，如果为None则使用默认名称
            
        Returns:
            设置字典
        """
        name = setting_name if setting_name else self.setting_name
        setting_path = self.get_setting_path(name)
        
        if not os.path.exists(setting_path):
            return self.create_default_setting()
        
        try:
            with open(setting_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # 尝试JSON格式（新格式）
                try:
                    setting = json.loads(content)
                except json.JSONDecodeError:
                    # 兼容旧格式：使用ast.literal_eval代替eval
                    import ast
                    setting = ast.literal_eval(content)
            return self._normalize_setting_keys(setting)
        except Exception as e:
            st.warning(f"读取设置文件失败: {e}，使用默认设置")
            return self.create_default_setting()
    
    def _normalize_setting_keys(self, setting: Dict[str, Any]) -> Dict[str, Any]:
        """标准化设置键名，兼容旧键名和新键名
        
        Args:
            setting: 原始设置字典
            
        Returns:
            标准化后的设置字典
        """
        normalized = {}
        # 键名映射：新键名 -> [可能的旧键名]
        key_mappings = {
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
            "segmentpos": []
        }
        
        for new_key, old_keys in key_mappings.items():
            # 优先使用新键名
            if new_key in setting:
                normalized[new_key] = setting[new_key]
            else:
                # 尝试旧键名
                for old_key in old_keys:
                    if old_key in setting:
                        normalized[new_key] = setting[old_key]
                        break
                else:
                    # 如果都不存在，使用默认值
                    normalized[new_key] = self._get_default_value(new_key)
        
        return normalized
    
    def _get_default_value(self, key: str) -> Any:
        """获取设置项的默认值
        
        Args:
            key: 设置项键名
            
        Returns:
            默认值
        """
        defaults = {
            "bar_color": DEFAULT_BAR_COLOR,
            "mw_color": DEFAULT_MW_COLOR,
            "bar_width": 1.2,
            "line_width": 1.0,
            "axis_width": 1.0,
            "title_font_size": 20,
            "axis_font_size": 14,
            "draw_bar": True,
            "draw_mw": True,
            "draw_table": True,
            "transparent_back": DEFAULT_TRANSPARENT_BACK,
            "segmentpos": [0, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000, 10000000, 50000000]
        }
        return defaults.get(key)
    
    def create_default_setting(self) -> Dict[str, Any]:
        """创建并保存默认设置
        
        Returns:
            默认设置字典
        """
        setting = {
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
            "draw_table": True
        }
        
        self.save_setting(setting, DEFAULT_SETTING_NAME)
        return setting
    
    def save_setting(self, setting: Dict[str, Any], name: Optional[str] = None) -> None:
        """保存设置到文件
        
        Args:
            setting: 设置字典
            name: 设置文件名，如果为None则使用默认名称
        """
        filename = name if name else self.setting_name
        setting_path = self.get_setting_path(filename)
        
        try:
            with open(setting_path, 'w', encoding='utf-8') as f:
                json.dump(setting, f, indent=2, ensure_ascii=False)
        except Exception as e:
            st.error(f"保存设置失败: {e}")
    
    def delete_setting(self, setting_name: str) -> None:
        """删除指定的设置文件
        
        Args:
            setting_name: 要删除的设置文件名
        """
        setting_path = self.get_setting_path(setting_name)
        try:
            os.remove(setting_path)
            # 如果删除后目录为空，创建默认设置
            if len(os.listdir(self.setting_dir)) == 0:
                self.create_default_setting()
        except Exception as e:
            st.error(f"删除设置失败: {e}")


class BaseAnalyzer:
    """分析器基类，包含共同的文件和目录操作方法"""
    
    def __init__(self, datadir: str):
        """初始化基类
        
        Args:
            datadir: 数据目录路径
        """
        self.rootdir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(self.rootdir, "datapath")
        self._cached_file_list: Optional[List[str]] = None
        self.lines: List[str] = []
        self.filename = ""
        self.sample_name = ""
        self.mw_data = []
        self.peak_num = 0
        self.peak_pos = []
        self.peak_data = {}
        
        # 集成日志器和验证器
        self.logger = logger  # 使用全局日志器实例
        self.validator = DataValidator(self.logger)
    
    def reset(self, reset_peak_data: bool = True) -> None:
        """重置所有数据属性
        
        Args:
            reset_peak_data: 是否重置 peak_data（GPC 需要累积多个文件的数据）
        """
        self.lines = []
        self.filename = ""
        self.sample_name = ""
        self.mw_data = []
        self.peak_num = 0
        self.peak_pos = []
        if reset_peak_data:
            self.peak_data = {}
    
    def clear_dir(self, output_dir: str) -> None:
        """清空输出目录
        
        Args:
            output_dir: 要清空的输出目录路径
        """
        if not os.path.exists(output_dir):
            return
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                st.warning(f"删除文件失败 {filename}: {e}")
    
    def read_file(self, name: str, reset_peak_data: bool = True) -> bool:
        """读取数据文件（优化版：使用生成器逐行读取）
        
        Args:
            name: 文件名
            reset_peak_data: 是否重置 peak_data（GPC 需要累积多个文件的数据）
            
        Returns:
            bool: 读取成功返回True，失败返回False
        """
        self.reset(reset_peak_data=reset_peak_data)
        file_path = os.path.join(self.data_path, name)
        
        try:
            # 优化：使用列表推导式和生成器，一次性过滤空行
            with open(file_path, "r", encoding="ascii") as file:
                self.lines = [line.strip() for line in file if line.strip()]
            return True
        except FileNotFoundError:
            self.logger.error(f"文件未找到: {name}", show_ui=True)
            return False
        except UnicodeDecodeError:
            self.logger.error(f"文件编码错误: {name}，请确保文件为ASCII编码", show_ui=True)
            return False
        except Exception as e:
            self.logger.error(f"读取文件失败 {name}", show_ui=True, exception=e)
            return False
    
    def read_file_list(self, force_refresh: bool = False) -> List[str]:
        """读取数据目录中的所有.rst文件列表（带缓存）
        
        Args:
            force_refresh: 强制刷新缓存
            
        Returns:
            文件名列表
        """
        if self._cached_file_list is None or force_refresh:
            self._cached_file_list = [os.path.basename(i) for i in glob.glob(os.path.join(self.data_path, "*.rst"))]
        return self._cached_file_list
    
    def preprocess_common(self) -> Tuple[int, int, int]:
        """预处理数据的公共部分，提取关键位置
        
        Returns:
            tuple: (mw_start, mw_end, slice_table_start)
        """
        mw_start = 0
        mw_end = 0
        slice_table_start = 0
        
        # 使用验证器验证数据行
        if not self.validator.validate_data_lines(self.lines):
            raise ValueError("数据文件为空，无法处理")
        
        # 一次遍历找到所有关键位置（优化：合并循环）
        for pos, line in enumerate(self.lines):
            if "Sample Name" in line:
                parts = line.split('\t')
                if len(parts) > 1:
                    self.sample_name = parts[1]
            elif "<MW_Averages>" in line:
                mw_start = pos
            elif "</MW_Averages>" in line:
                mw_end = pos
            elif "<Slice_Table>" in line:
                slice_table_start = pos
                break  # 找到最后一个标记后退出

        # 使用验证器验证标记
        if not self.validator.validate_markers(mw_start, mw_end, slice_table_start):
            raise ValueError("数据文件格式错误")
        
        return mw_start, mw_end, slice_table_start

class MolecularWeightAnalyzer(BaseAnalyzer):
    def __init__(self, datadir: str, save_file: bool = True, bar_width: float = 1.2, line_width: float = 1.0, axis_width: float = 1.0,
                 title_font_size: float = 20, axis_font_size: float = 14, transparent_back: bool = DEFAULT_TRANSPARENT_BACK, save_picture: bool = True, display_picture: bool = False, 
                 bar_color: str = DEFAULT_BAR_COLOR, mw_color: str = DEFAULT_MW_COLOR, draw_bar: bool = True, draw_mw: bool = True, draw_table: bool = True, 
                 setting_name: str = DEFAULT_SETTING_NAME, test_mode: bool = False, progress_callback: Optional[Callable[[float, str], None]] = None) -> None:
        # 调用基类构造函数
        super().__init__(datadir)
        self.output_dir = os.path.join(self.rootdir, "Mw_output")
        self.setting_dir = os.path.join(self.rootdir, "setting")
        self.file_list : Optional[List[str]] = None
        self.selected_file = None
        
        # 每个文件的数据存储
        self.norm = None
        self.mw = None
        
        # 进度回调函数
        self.progress_callback = progress_callback

        # 初始化设置管理器
        self.settings_manager = SettingsManager(self.setting_dir, setting_name)
        
        # 读取设置
        self.setting_name = setting_name
        if "settingname" not in st.session_state:
            st.session_state["settingname"] = self.setting_name
        else:
            self.setting_name = st.session_state["settingname"]
        
        setting = self.settings_manager.load_setting(self.setting_name)
        
        # 初始化绘图属性
        self.bar_color = setting.get("bar_color", DEFAULT_BAR_COLOR)
        self.mw_color = setting.get("mw_color", DEFAULT_MW_COLOR)
        self.transparent_back = setting.get("transparent_back", DEFAULT_TRANSPARENT_BACK)
        self.bar_width = setting.get("bar_width", 1.2)
        self.line_width = setting.get("line_width", 1.0)
        self.axis_width = setting.get("axis_width", 1.0)
        self.title_font_size = setting.get("title_font_size", 20)
        self.axis_font_size = setting.get("axis_font_size", 14)
        self.draw_bar = setting.get("draw_bar", True)
        self.draw_mw = setting.get("draw_mw", True)
        self.draw_table = setting.get("draw_table", True)
        
        # 初始化分段位置
        if "segmentpos" not in st.session_state:
            self.segmentpos = setting.get("segmentpos", [0, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000, 10000000, 50000000])
            st.session_state["segmentpos"] = self.segmentpos
        else:
            self.segmentpos = st.session_state["segmentpos"]
        
        if "selectedpos" not in st.session_state:
            self.selectedpos = self.segmentpos
            st.session_state["selectedpos"] = self.segmentpos
        else:
            self.selectedpos = st.session_state["selectedpos"]
        
        self.segmentnum = len(self.segmentpos)

        # 运行模式
        self.test_mode = test_mode
        self.save_file = save_file
        self.save_picture = save_picture
        self.display_picture = display_picture

    def clear_dir(self):
        """清空输出目录"""
        super().clear_dir(self.output_dir)

    def check_dir(self) -> bool:
        """检查输出目录中是否存在同名文件
        
        Returns:
            bool: 存在同名文件返回True
        """
        for file in self.selected_file:
            if os.path.exists(os.path.join(self.output_dir, file.split('.')[0] + '.png')):
                return True
        return False    

    def setting_list(self) -> List[str]:
        """获取所有设置文件列表
        
        Returns:
            设置文件名列表
        """
        return self.settings_manager.list_settings()

    def save_setting(self, new_setting_name: str = '') -> None:
        """保存当前设置到文件
        
        Args:
            new_setting_name: 新设置文件名
        """
        setting = {
            "segmentpos": self.selectedpos,
            "bar_color": self.bar_color,
            "mw_color": self.mw_color,
            "transparent_back": self.transparent_back,
            "bar_width": self.bar_width,
            "line_width": self.line_width,
            "axis_width": self.axis_width,
            "title_font_size": self.title_font_size,
            "axis_font_size": self.axis_font_size,
            "draw_bar": self.draw_bar,
            "draw_mw": self.draw_mw,
            "draw_table": self.draw_table
        }
        
        self.settings_manager.save_setting(setting, new_setting_name)
        st.session_state["segmentpos"] = self.selectedpos
        st.session_state["selectedpos"] = self.selectedpos
                        
    def delete_setting(self, settingname: str) -> None:
        """删除指定的设置文件
        
        Args:
            settingname: 要删除的设置文件名
        """
        self.settings_manager.delete_setting(settingname)
            
    def change_setting(self, settingname: str) -> None:
        """切换到指定的设置
        
        Args:
            settingname: 设置文件名
        """
        st.session_state["settingname"] = self.setting_name
        return

    def add_region(self, new_region: int) -> None:
        """添加新的分子量区间分割点
        
        Args:
            new_region: 新的分割点值
        """
        self.segmentpos.append(new_region)
        self.segmentpos.sort()
    
    def read_file(self, name: str) -> bool:
        """读取数据文件（优化版：使用列表推导式）
        
        Args:
            name: 文件名
            
        Returns:
            bool: 读取成功返回True，失败返回False
        """
        self.reset()
        file_path = os.path.join(self.data_path, name)
        
        try:
            # 优化：使用列表推导式和生成器，一次性过滤空行
            with open(file_path, "r", encoding="ascii") as file:
                self.lines = [line.strip() for line in file if line.strip()]
            return True
        except FileNotFoundError:
            self.logger.error(f"文件未找到: {name}", show_ui=True)
            return False
        except UnicodeDecodeError:
            self.logger.error(f"文件编码错误: {name}，请确保文件为ASCII编码", show_ui=True)
            return False
        except Exception as e:
            self.logger.error(f"读取文件失败 {name}", show_ui=True, exception=e)
            return False
        
    def preprocess(self) -> None:
        """预处理数据文件，提取分子量和峰数据"""
        # 调用基类的公共预处理
        mw_start, mw_end, slice_table_start = self.preprocess_common()

        # 整理分子量数据
        for line in self.lines[mw_start + MW_DATA_OFFSET:mw_end]:
            parts = line.split('\t')
            if len(parts) > 1:
                self.mw_data.append([self.sample_name] + parts[1:])
        
        if not self.mw_data:
            raise ValueError("未找到分子量数据")
        
        self.peak_num = len(self.mw_data)
        
        # 提取峰数据
        current_peak = []
        all_peaks = []
        for line in self.lines[slice_table_start + 1:]:
            if ("Peak" in line and len(current_peak) > 1) or '</Slice_Table>' in line:
                try:
                    peak_array = np.array(current_peak[1:], dtype="float")
                    # 验证数组形状
                    if peak_array.shape[0] > 0 and peak_array.shape[1] > MIN_PEAK_COLUMNS:
                        self.norm = peak_array[:, NORM_COLUMN_INDEX]
                        self.mw = peak_array[:, MW_COLUMN_INDEX]
                        all_peaks.append(peak_array)
                    else:
                        st.warning(f"峰数据格式不正确，跳过该峰")
                except (ValueError, IndexError) as e:
                    st.warning(f"峰数据转换失败: {e}")
                current_peak = []
                continue
            if "RT" in line:
                continue
            line_parts = line.split('\t')[:-1]
            if line_parts and "-2" in line_parts[0]:
                continue
            current_peak.append(line_parts)
        
        if not all_peaks:
            raise ValueError("未找到有效的峰数据")
        
        self.peak_data = all_peaks

    def transform_number(self, num: float) -> str:
        """将数字转换为科学记数法格式
        
        Args:
            num: 要转换的数字
            
        Returns:
            科学记数法字符串
        """
        dig = len(str(num)) - 1
        front = num / (10 ** dig)
        return '{:.1f} × 10$^{}$'.format(front, dig)
    
    def start_width(self) -> int:
        """计算起始宽度
        
        Returns:
            宽度值
        """
        return (len(str(self.segmentpos[1])) - 2) * 2
    
    def _validate_draw_data(self) -> None:
        """验证绘图所需的数据完整性
        
        Raises:
            ValueError: 数据不完整时抛出异常
        """
        if not self.validator.validate_data_not_empty(self.norm, "归一化数据"):
            raise ValueError(f"文件 {self.filename}: 没有可用的归一化数据")
        if not self.validator.validate_data_not_empty(self.mw, "分子量数据"):
            raise ValueError(f"文件 {self.filename}: 没有可用的分子量数据")
        if not self.validator.validate_segment_positions(self.selectedpos):
            raise ValueError("至少需要2个分割位置")
    
    def _calculate_segment_percentages(self) -> List[float]:
        """计算各分子量区间的百分比
        
        Returns:
            List[float]: 各区间百分比列表
        """
        segment_percentages = []
        for segment_idx in range(len(self.selectedpos) - 1):
            lower_bound = self.selectedpos[segment_idx]
            upper_bound = self.selectedpos[segment_idx + 1]
            mask = (self.mw < upper_bound) & (self.mw > lower_bound)
            segment_sum = np.sum(self.norm[np.where(mask)]) * PERCENTAGE_FACTOR
            segment_percentages.append(segment_sum)
        self.logger.debug(f"计算区间百分比: {segment_percentages}")
        return segment_percentages
    
    def _setup_figure(self) -> Tuple[Any, Any, Any]:
        """设置并创建图形对象
        
        Returns:
            Tuple: (fig, ax, gs) 图形、坐标轴和GridSpec对象
        """
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
        
        if self.draw_table:
            fig = plt.figure(dpi=FIGURE_DPI, figsize=FIGURE_SIZE_WITH_TABLE)
        else:
            fig = plt.figure(dpi=FIGURE_DPI, figsize=FIGURE_SIZE_WITHOUT_TABLE)

        if self.transparent_back:
            fig.patch.set_alpha(0.0)
        
        gs = gridspec.GridSpec(GRIDSPEC_ROWS, GRIDSPEC_COLS)
        if not self.draw_table:
            ax = fig.add_subplot(gs[:, :])  
        else:   
            ax = fig.add_subplot(gs[:, :5])
        
        return fig, ax, gs
    
    def _plot_data(self, ax: Any, segment_percentages: List[float]) -> None:
        """绘制分子量分布曲线和柱状图
        
        Args:
            ax: matplotlib坐标轴对象
            segment_percentages: 各区间百分比
        """
        import matplotlib.pyplot as plt
        
        # 计算柱状图位置和宽度
        bar_positions = [
            (self.selectedpos[idx] * BAR_POSITION_WEIGHT_LEFT + 
             self.selectedpos[idx + 1] * BAR_POSITION_WEIGHT_RIGHT) 
            for idx in range(len(self.selectedpos) - 1)
        ]
        bar_widths = [pos * self.bar_width for pos in bar_positions]
        
        # 归一化数据
        max_norm = max(self.norm)
        if max_norm > 0:  # 避免除以零
            normalized_data = [value * NORM_SCALE_FACTOR / max_norm for value in self.norm]
        else:
            normalized_data = [0] * len(self.norm)
            self.logger.warning(f"文件 {self.filename}: 归一化数据最大值为0")
        
        # 设置坐标轴粗细
        for spine in ax.spines.values():
            spine.set_linewidth(self.axis_width)
        
        # 绘制曲线和柱状图
        if self.draw_mw:
            ax.plot(self.mw, normalized_data, color=self.mw_color, linewidth=self.line_width)
        if self.draw_bar:
            ax.bar(bar_positions, segment_percentages, align="edge", width=bar_widths, color=self.bar_color)

        # 设置图形样式
        plt.xscale("log")
        font1 = {"size": self.axis_font_size, "weight":"bold", "fontname": "Arial"}
        font2 = {"size": self.title_font_size, "weight":"bold", "fontname": "Arial"}
        plt.xlabel("Mw (g /mol)", labelpad = 4, fontdict = font1)
        plt.ylabel("Cumulative%", labelpad = 4, fontdict = font1)
        plt.xticks(weight = 'bold')
        plt.yticks(weight = 'bold')
        
        result_name = self.filename.split('.')[0]
        plt.title(result_name, pad = 10, fontdict = font2)
    
    def _create_distribution_table(self, fig: Any, gs: Any, segment_percentages: List[float]) -> None:
        """创建分子量区间分布表格
        
        Args:
            fig: matplotlib图形对象
            gs: GridSpec对象
            segment_percentages: 各区间百分比
        """
        from plottable import Table, ColumnDefinition
        
        ax1 = fig.add_subplot(gs[:6, 5:7])
        distribution_data = []
    
        for segment_idx, pos in enumerate(self.selectedpos[1:-1]):
            if segment_idx == 0:
                range_label = "< " + self.transform_number(self.selectedpos[segment_idx + 1])
            elif segment_idx == len(self.selectedpos[1:-1]) - 1:
                range_label = ">" + self.transform_number(self.selectedpos[segment_idx])
            else:
                range_label = self.transform_number(self.selectedpos[segment_idx]) + " ~ " + self.transform_number(self.selectedpos[segment_idx + 1])
            percentage_text = "{:.2f}%".format(segment_percentages[segment_idx])
            distribution_data.append([range_label, percentage_text])
        
        df_distribution = pd.DataFrame(data=distribution_data, columns=["Mw", "Percent"]).set_index("Mw")
        Table(df_distribution, 
            ax=ax1, 
            textprops={"fontsize": 12, "fontname": 'Times New Roman'},
            column_definitions=[
                ColumnDefinition(name="Mw", width=10, textprops={"ha": "center"}),
                ColumnDefinition(name="Percent", width=4, textprops={"ha": "center"})
            ],
            footer_divider=True,
            row_dividers=True
        )
    
    def _create_stats_table(self, fig: Any, gs: Any) -> None:
        """创建分子量统计数据表格
        
        Args:
            fig: matplotlib图形对象
            gs: GridSpec对象
        """
        from plottable import Table, ColumnDefinition
        
        stats_data = []
        ax2 = fig.add_subplot(gs[7, 5:7])
        
        # 验证数据完整性
        if (self.mw_data and len(self.mw_data) > 0 and 
            self.validator.validate_array_shape(
                np.array(self.mw_data), min_rows=1, min_cols=MIN_MW_DATA_COLUMNS, name="分子量数据")):
            for mw_row in self.mw_data:
                if len(mw_row) >= MIN_MW_DATA_COLUMNS:
                    # 索引 2=Mn, 3=Mw, 7=PDI
                    stats_data.append([self.mw_data[0][2], self.mw_data[0][3], self.mw_data[0][7]])
                else:
                    self.logger.warning("分子量数据不完整，跳过表格生成", show_ui=True)
                    break
        else:
            self.logger.warning("分子量数据格式错误，跳过表格生成", show_ui=True)
        
        if stats_data:
            df_stats = pd.DataFrame(data=stats_data, columns=["Mn", "Mw", "PDI"]).set_index("Mn")
            Table(df_stats,
                ax=ax2,
                textprops={"fontsize": 12, "fontname": 'Times New Roman'},
                column_definitions=[
                    ColumnDefinition(name="Mw", textprops={"ha": "center"}),
                    ColumnDefinition(name="Mn", textprops={"ha": "center"}),
                    ColumnDefinition(name="PDI", textprops={"ha": "center"})
                ])

    def draw_image(self) -> None:
        """绘制分子量分布图（重构版：调用多个子方法）"""
        # 延迟导入 matplotlib,减少启动时间和打包体积
        import matplotlib.pyplot as plt
        
        # 步骤1: 验证数据
        self._validate_draw_data()
        
        # 步骤2: 计算区间百分比
        segment_percentages = self._calculate_segment_percentages()
        
        # 使用 try-finally 确保资源释放
        fig = None
        try:
            # 步骤3: 设置图形
            fig, ax, gs = self._setup_figure()
            
            # 步骤4: 绘制数据
            self._plot_data(ax, segment_percentages)
            
            # 步骤5: 绘制表格（如果需要）
            if self.draw_table:
                self._create_distribution_table(fig, gs, segment_percentages)
                self._create_stats_table(fig, gs)
            
            # 步骤6: 保存和显示
            result_name = self.filename.split('.')[0]
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, exist_ok=True)
            if self.save_picture:
                plt.savefig(os.path.join(self.output_dir, result_name + ".png"), transparent = self.transparent_back)
                self.logger.debug(f"已保存图片: {result_name}.png")
            if self.display_picture:
                st.pyplot(fig, width='content')
        finally:
            # 确保图形资源释放
            if fig is not None:
                plt.close(fig)
        return
    
    def output_data(self):
        column = ["Samplename", "Mp", "Mn", "Mw", "Mz", "Mz+1", "Mv",  "PD"]

    def run(self) -> bool:
        """运行分析流程
        
        处理所有选中的文件，生成分子量分布图
        
        Returns:
            bool: 成功返回True
        """
        if len(self.selected_file) == 0:
            self.logger.warning("没有选中文件", show_ui=True)
            return False
        
        self.file_list = self.selected_file
        
        for pro, filename in enumerate(self.file_list):
            self.filename = filename
            try:
                if self.read_file(filename):
                    self.preprocess()
                    self.draw_image()
                    self.logger.info(f"成功处理文件: {filename}")
            except Exception as e:
                self.logger.error(f"处理文件 {filename} 时出错", show_ui=True, exception=e)
                # 继续处理下一个文件
                continue
            finally:
                # 进度回调
                if self.progress_callback:
                    self.progress_callback((pro + 1) / len(self.file_list), "画图进度 {}/{} {:.2f}%".format(pro + 1, len(self.file_list), (pro + 1) * 100/ len(self.file_list)))
        
        return True

class GPCAnalyzer(BaseAnalyzer):
    def __init__(self, datadir: str, output_filename: str, save_file: bool = True, save_picture: bool = True, display_mode: bool = True, save_figure_file_gpc: bool = True, test_mode: bool = False, progress_callback: Optional[Callable[[float, str], None]] = None, info_callback: Optional[Callable[[str], None]] = None) -> None:
        # 调用基类构造函数
        super().__init__(datadir)
        self.output_dir = os.path.join(self.rootdir, "GPC_output")
        self.file_list = None
        self.output_filename = output_filename
        self.selected_file = None

        # 运行模式
        self.test_mode = test_mode
        self.save_file = save_file
        self.save_picture = save_picture
        self.display_mode = display_mode
        self.save_figure_file_gpc = save_figure_file_gpc
        
        # 回调函数
        self.progress_callback = progress_callback
        self.info_callback = info_callback

        #画图颜色库
        from cnames import clist
        self.color_list = clist

    def clear_dir(self):
        """清空输出目录"""
        super().clear_dir(self.output_dir)

    def check_dir(self) -> bool:
        """检查输出目录中是否存在同名文件
        Returns:
            bool: 存在同名文件返回True
        """
        if os.path.exists(os.path.join(self.output_dir, self.output_filename + '.csv')) or os.path.exists(os.path.join(self.output_dir, self.output_filename + '.png')):
            return True
        return False
    
    def preprocess(self) -> None:
        """预处理数据文件，提取分子量和峰数据"""
        # 调用基类的公共预处理
        mw_start, mw_end, slice_table_start = self.preprocess_common()

        # 整理分子量数据
        for line in self.lines[mw_start + MW_DATA_OFFSET:mw_end]:
            parts = line.split('\t')
            if len(parts) > 1:
                self.mw_data.append([self.sample_name] + parts[1:])
        
        if not self.mw_data:
            raise ValueError("未找到分子量数据")
        
        self.peak_num = len(self.mw_data)
        
        # 提取峰数据
        current_peak = []
        all_peaks = []
        for line in self.lines[slice_table_start + 1:]:
            if ("Peak" in line and len(current_peak) > 1) or '</Slice_Table>' in line:
                try:
                    peak_array = np.array(current_peak[1:], dtype="float")
                    # 验证数组形状
                    if peak_array.shape[0] > 0 and peak_array.shape[1] > MIN_GPC_PEAK_COLUMNS:
                        all_peaks.append(peak_array)
                    else:
                        st.warning(f"文件 {self.filename}: 峰数据格式不正确，跳过该峰")
                except (ValueError, IndexError) as e:
                    st.warning(f"文件 {self.filename}: 峰数据转换失败: {e}")
                current_peak = []
                continue
            if "RT" in line:
                continue
            line_parts = line.split('\t')[:-1]
            if line_parts and "-2" in line_parts[0]:
                continue
            current_peak.append(line_parts)
        
        if not all_peaks:
            raise ValueError("未找到有效的峰数据")
        
        self.peak_data[self.sample_name] = all_peaks

    def draw_image(self) -> None:
        # 延迟导入 matplotlib,减少启动时间和打包体积
        import matplotlib.pyplot as plt
        
        # 验证数据是否存在
        if not self.peak_data:
            raise ValueError("没有可用的峰数据用于绘图")
        
        # 使用 try-finally 确保资源释放
        fig = None
        try:
            fig = plt.figure(dpi=FIGURE_DPI, figsize=GPC_FIGURE_SIZE)
            plotted_labels = []
            for sample_idx, (sample_name, peak_data_list) in enumerate(self.peak_data.items()):
                if sample_idx >= len(self.color_list):
                    st.warning(f"颜色库不足，跳过样品 {sample_name}")
                    break
                for peak_array in peak_data_list:
                    if peak_array.shape[1] <= MIN_GPC_PEAK_COLUMNS:
                        st.warning(f"样品 {sample_name} 的峰数据不完整，跳过")
                        continue
                    x_data = peak_array[:, GPC_X_COLUMN_INDEX]
                    y_data = peak_array[:, GPC_Y_COLUMN_INDEX]
                    plt.plot(x_data, y_data, c=self.color_list[sample_idx], label=sample_name)
                    plotted_labels.append(sample_name)
            
            if not plotted_labels:
                raise ValueError("没有有效数据可以绘图")
            
            plt.legend(plotted_labels)
            result_name = self.output_filename
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, exist_ok=True)
            if self.save_picture:
                plt.savefig(os.path.join(self.output_dir, result_name + ".png"))
            if self.display_mode:
                st.pyplot(fig)
        finally:
            # 确保图形资源释放
            if fig is not None:
                plt.close(fig)
        return

    def output_data(self):
        column = ["Samplename", "Mp", "Mn", "Mw", "Mz", "Mz+1", "Mv",  "PD"]
        result_name = self.output_filename
        data  = pd.DataFrame(data = self.mw_data, columns = column)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
        if self.save_file:
            data.to_csv(os.path.join(self.output_dir, result_name + '.csv'))

    def output_figure_data(self) -> None:
        result_name = os.path.join(self.output_dir, self.output_filename + ".xlsx")
        xlsx = pd.ExcelWriter(result_name, engine = "openpyxl")
        for num, (name, data) in enumerate(self.peak_data.items()):
            for peak in data:
                x = peak[:,5]
                y = peak[:,6]
                df = pd.DataFrame(peak[:,5:7])
                df.to_excel(xlsx, sheet_name = name, index = False, header = False)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
        xlsx.close()

    def run(self) -> bool:
        """运行GPC分析流程
        
        Returns:
            bool: 成功返回True，失败返回False
        """
        if self.selected_file == None:
            self.file_list = [os.path.basename(i) for i in glob.glob(os.path.join(self.data_path, "*.rst"))]
        else:
            self.file_list = self.selected_file

        # 在开始处理前清空 peak_data，确保不会累积旧数据
        self.peak_data = {}
        
        for pro, filename in enumerate(self.file_list):
            self.filename = filename
            try:
                # 使用 reset_peak_data=False 保留之前文件的 peak_data
                if self.read_file(filename, reset_peak_data=False):
                    self.preprocess()
                    self.logger.info(f"成功处理文件: {filename}")
            except Exception as e:
                self.logger.error(f"处理文件 {filename} 时出错", show_ui=True, exception=e)
                # 继续处理下一个文件
            finally:
                if self.progress_callback:
                    self.progress_callback((pro + 1) / len(self.file_list), "画图进度 {}/{} {:.2f}%".format(pro + 1, len(self.file_list), (pro + 1) * 100/ len(self.file_list)))
        
        if self.info_callback:
            self.info_callback("绘制图片")
        try:
            self.draw_image()
        except Exception as e:
            self.logger.error("绘图失败", show_ui=True, exception=e)
            return False
        
        if self.info_callback:
            self.info_callback("保存数据")
        try:
            if self.save_file:
                self.output_data()
            if self.save_figure_file_gpc:
                self.output_figure_data()
        except Exception as e:
            self.logger.error("保存数据失败", show_ui=True, exception=e)
            return False
        
        return True


# 主程序入口
if __name__ == "__main__":
    # 导入并运行UI
    from ui import render_app
    render_app()
