"""
DSCAnalyzer — DSC (Differential Scanning Calorimetry) data processor.

Extracted from the monolithic main.py for the v2 refactoring.
All Streamlit dependencies have been removed; UI feedback is handled via callbacks.
"""

import os
import re
import glob
import numpy as np
import chardet
import matplotlib.pyplot as plt

from typing import List, Optional, Tuple, Callable, Dict, Any

from .base import (
    BaseAnalyzer,
    SettingsManager,
    Logger,
    logger,
    DEFAULT_BAR_COLOR,
    DEFAULT_DSC_SETTING_NAME,
    DEFAULT_TRANSPARENT_BACK,
    FIGURE_DPI,
    FIGURE_SIZE_WITHOUT_TABLE,
)

# Color palette for cycle overlay plots.
# Try importing from the project-level ``cnames`` module; fall back to a
# built-in matplotlib tab palette so the analyser works stand-alone.
try:
    from cnames import clist as _COLOR_LIST  # type: ignore[import-untyped]
except ImportError:
    _COLOR_LIST: List[str] = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]


class DSCAnalyzer(BaseAnalyzer):
    """DSC分析器 - 处理DSC数据"""

    def __init__(
        self,
        datadir: str,
        test_mode: bool = False,
        save_seg_mode: bool = True,
        draw_seg_mode: bool = True,
        draw_cycle: bool = True,
        display_pic: bool = True,
        save_cycle_pic: bool = True,
        peaks_upward: bool = False,
        center_peak: bool = False,
        left_length: float = 1.9,
        right_length: float = 1.9,
        setting_name: str = DEFAULT_DSC_SETTING_NAME,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        info_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """初始化DSC分析器"""
        super().__init__(datadir)

        self.cycle_dir: str = os.path.join(os.path.dirname(self.data_path), "DSC_Cycle")
        self.pic_dir: str = os.path.join(os.path.dirname(self.data_path), "DSC_Pic")
        self.setting_dir: str = os.path.join(self.rootdir, "setting")

        self.heads: Dict[int, str] = {}
        self.method: Dict[int, Tuple[float, float, float, float]] = {}
        self.cycle: List[List[int]] = []
        self.data_seg: List[np.ndarray] = []
        self.region: List[List[float]] = []
        self.peak: List[List[str]] = []
        self.data: Optional[np.ndarray] = None

        # 运行模式设置
        self.test_mode: bool = test_mode
        self.save_seg_mode: bool = save_seg_mode
        self.draw_seg_mode: bool = draw_seg_mode
        self.draw_cycle: bool = draw_cycle
        self.display_pic: bool = display_pic
        self.save_cycle_pic: bool = save_cycle_pic
        self.peaks_upward: bool = peaks_upward
        self.center_peak: bool = center_peak

        # 参数设置
        self.left_length: float = left_length
        self.right_length: float = right_length

        # 回调函数
        self.progress_callback = progress_callback
        self.info_callback = info_callback

        # 颜色库
        self.color_list: List[str] = _COLOR_LIST

        # 初始化设置管理器
        default_setting: Dict[str, Any] = {
            "curve_color": DEFAULT_BAR_COLOR,
            "transparent_back": DEFAULT_TRANSPARENT_BACK,
            "line_width": 1.0,
            "axis_width": 1.0,
            "title_font_size": 20,
            "axis_font_size": 14,
        }
        self.settings_manager = SettingsManager(
            self.setting_dir, setting_name, default_setting
        )

        # 读取设置
        self.setting_name: str = setting_name
        setting = self.settings_manager.load_setting(self.setting_name)

        # 初始化绘图属性
        self.curve_color: str = setting.get("curve_color", DEFAULT_BAR_COLOR)
        self.transparent_back: bool = setting.get(
            "transparent_back", DEFAULT_TRANSPARENT_BACK
        )
        self.line_width: float = setting.get("line_width", 1.0)
        self.axis_width: float = setting.get("axis_width", 1.0)
        self.title_font_size: int = setting.get("title_font_size", 20)
        self.axis_font_size: int = setting.get("axis_font_size", 14)

    # -- settings ----------------------------------------------------------

    def setting_list(self) -> List[str]:
        """获取所有设置文件列表"""
        return self.settings_manager.list_settings()

    def save_setting(self, new_setting_name: str = "") -> None:
        """保存当前设置到文件"""
        setting: Dict[str, Any] = {
            "curve_color": self.curve_color,
            "transparent_back": self.transparent_back,
            "line_width": self.line_width,
            "axis_width": self.axis_width,
            "title_font_size": self.title_font_size,
            "axis_font_size": self.axis_font_size,
        }
        self.settings_manager.save_setting(setting, new_setting_name)

    def delete_setting(self, settingname: str) -> None:
        """删除指定的设置文件"""
        self.settings_manager.delete_setting(settingname)

    def change_setting(self, settingname: str) -> None:
        """切换到指定的设置"""
        self.setting_name = settingname

    # -- reset / clear -----------------------------------------------------

    def reset(self, reset_peak_data: bool = True) -> None:
        """重置数据"""
        super().reset(reset_peak_data)
        self.heads = {}
        self.method = {}
        self.cycle = []
        self.data_seg = []
        self.region = []
        self.peak = []
        self.data = None

    def clear_dir(self) -> None:  # type: ignore[override]
        """清空输出目录"""
        # 清空 Cycle 目录
        for cycle_dir in glob.glob(os.path.join(self.cycle_dir, "Cycle*")):
            try:
                for file in os.listdir(cycle_dir):
                    file_path = os.path.join(cycle_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                if os.path.exists(cycle_dir):
                    os.rmdir(cycle_dir)
            except Exception as e:
                self.logger.warning(f"清理目录失败 {cycle_dir}: {e}")

        # 清空 Pic 目录
        if os.path.exists(self.pic_dir):
            for dir_name in os.listdir(self.pic_dir):
                dir_path = os.path.join(self.pic_dir, dir_name)
                try:
                    if os.path.isdir(dir_path):
                        for file in os.listdir(dir_path):
                            os.remove(os.path.join(dir_path, file))
                        os.rmdir(dir_path)
                except Exception as e:
                    self.logger.warning(f"清理目录失败 {dir_path}: {e}")

    # -- file I/O ----------------------------------------------------------

    def read_file(self, name: str, reset_peak_data: bool = True) -> bool:
        """读取数据文件 (自动检测编码)"""
        self.reset()
        self.filename = name
        file_path = os.path.join(self.data_path, name)

        try:
            # 检测编码
            with open(file_path, "rb") as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result["encoding"]
                # 如果置信度太低，或者检测失败，回退到 utf-16 (常见于 DSC) 或 utf-8
                if not encoding or result["confidence"] < 0.5:
                    if raw_data.startswith(b"\xff\xfe") or raw_data.startswith(
                        b"\xfe\xff"
                    ):
                        encoding = "utf-16"
                    else:
                        encoding = "utf-8"

            self.logger.debug(f"文件 {name} 检测到的编码: {encoding}")

            with open(file_path, "r", encoding=encoding, errors="replace") as file:
                self.lines = [line.strip() for line in file if line.strip()]
            return True
        except Exception as e:
            self.logger.error(f"读取文件失败 {name}", show_ui=True, exception=e)
            return False

    # -- preprocessing -----------------------------------------------------

    def preprocess(self) -> None:
        """预处理数据"""
        table_pos: int = 0
        peak_pos: int = 0
        org_method: List[str] = []

        # 找到表头
        for pos, line in enumerate(self.lines):
            if "Peak" in line:
                peak_pos = pos + 3
            if "Sig" in line:
                l = line.split()
                if len(l) > 1:
                    title = " ".join(l[1:-1])
                    unit = l[-1]
                    try:
                        idx = int(l[0][3:])
                        self.heads[idx] = title + "/" + unit
                    except ValueError:
                        pass
            if "OrgMethod" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    org_method.append(parts[1])
            if "StartOfData" in line:
                table_pos = pos
                break

        # 优化正则：只匹配数字
        re_float = re.compile(r"(-?\d+\.\d+)")

        end: float = 0.0
        cycle: List[int] = []
        start: float = 0.0

        # 记录每个 cycle 的结束时间（累积）
        accumulated_time: float = 0.0
        cycle_end_times: List[float] = []

        # 分类方法
        for item, m in enumerate(org_method):
            grad: float = 0.0
            t: float = 0.0

            # 提取行中所有浮点数
            nums = [float(n) for n in re.findall(re_float, m)]

            if "Equilibrate" in m:
                start = end
                if nums:
                    end = nums[0]
                self.cycle.append([item])
            elif "Ramp" in m:
                start = end
                if len(nums) >= 2:
                    grad = nums[0]
                    end = nums[1]
                elif len(nums) == 1:
                    end = nums[0]

                if start > end:
                    grad = -abs(grad)
                else:
                    grad = abs(grad)

                if grad != 0:
                    t = abs(end - start) / abs(grad)

                cycle.append(item)
                accumulated_time += t
            elif "Isothermal" in m:
                start = end
                if nums:
                    t = nums[0]
                cycle.append(item)
                accumulated_time += t
            elif "Mark" in m:
                cycle.append(item)
                self.cycle.append(cycle)
                cycle = []
                start = end
                cycle_end_times.append(accumulated_time)

            # 记录方法
            self.method[item] = (start, end, grad, t)

        if table_pos + 1 < len(self.lines):
            try:
                start_time = float(self.lines[table_pos + 1].split("\t")[0])
                if 1 in self.method:
                    start_time += self.method[1][3]
            except (ValueError, IndexError):
                start_time = 0.0
        else:
            start_time = 0.0

        # 整理数据格式
        table: List[List[str]] = []
        current_start_time: float = start_time
        count_cycle: int = 3

        data_lines = self.lines[table_pos + 1 :]

        for pos, line in enumerate(data_lines):
            l = line.split("\t")
            is_separator = False
            if l and len(l) > 0:
                val_str = l[0].strip()
                if val_str.startswith("-2"):
                    is_separator = True

            if is_separator:
                try:
                    if table:
                        end_time = float(table[-1][0])
                    else:
                        end_time = current_start_time

                    left_side = current_start_time + self.left_length
                    right_side = end_time - self.right_length
                    if count_cycle in self.method:
                        right_side -= self.method[count_cycle][3]

                    self.region.append([left_side, right_side])

                    if pos + 1 < len(data_lines):
                        next_line = data_lines[pos + 1]
                        next_l = next_line.split("\t")
                        if next_l and len(next_l) > 0:
                            current_start_time = float(next_l[0])

                    count_cycle += 3
                except (ValueError, IndexError):
                    pass
                continue

            # 只有非分隔符行才加入 table
            if len(l) >= 2:
                table.append(l)

        # 处理最后一个区域
        if table:
            try:
                last_time = float(table[-1][0])
                left_side = current_start_time + self.left_length
                right_side = last_time - self.right_length
                self.region.append([left_side, right_side])
            except (ValueError, IndexError):
                pass

        if peak_pos != 0:
            for i in range(len(self.region) - 1):
                if peak_pos + i < len(self.lines):
                    self.peak.append(
                        list(filter(None, self.lines[peak_pos + i].split(" ")))
                    )

        try:
            valid_table = [row for row in table if len(row) >= 2]
            self.data = np.array(valid_table, dtype="float32")

            for region in self.region:
                left_side, right_side = region
                if self.data.size > 0 and self.data.shape[1] > 0:
                    segment = self.data[
                        np.where(
                            (self.data[:, 0] > left_side)
                            & (self.data[:, 0] < right_side)
                        )
                    ]
                    self.data_seg.append(segment)
        except ValueError as e:
            self.logger.error(f"数据转换失败: {e}")

    # -- data export -------------------------------------------------------

    def save_data_seg(self) -> None:
        """保存切片数据"""
        for i in range(len(self.region)):
            cycle_path = os.path.join(self.cycle_dir, f"Cycle{i + 1}")
            if not os.path.exists(cycle_path):
                os.makedirs(cycle_path, exist_ok=True)

            filename = os.path.join(
                cycle_path, os.path.splitext(self.filename)[0] + ".csv"
            )
            if i < len(self.data_seg):
                try:
                    np.savetxt(filename, self.data_seg[i][:, 1:3], delimiter=",")
                except Exception as e:
                    self.logger.error(f"保存切片数据失败: {e}")

    # -- drawing -----------------------------------------------------------

    def draw_img(self) -> None:
        """绘制切片图"""
        for num, data in enumerate(self.data_seg):
            if data.size == 0:
                continue

            plt.cla()
            fig = plt.figure(dpi=FIGURE_DPI, figsize=FIGURE_SIZE_WITHOUT_TABLE)
            if self.transparent_back:
                fig.patch.set_alpha(0.0)

            ax = fig.add_subplot(111)

            x = data[:, 1]
            y = data[:, 2]

            # 如果勾选了峰始终向上
            if self.peaks_upward and len(x) > 1:
                # 升温(吸热)峰向下 → 翻转Y轴使峰向上
                if x[-1] > x[0]:
                    y = -y

            # 如果勾选了峰居中
            if self.center_peak and len(x) > 1:
                peak_idx: int = 0
                if self.peaks_upward:
                    peak_idx = int(np.argmax(y))
                else:
                    y_centered = y - np.median(y)
                    if np.abs(np.min(y_centered)) > np.abs(np.max(y_centered)):
                        peak_idx = int(np.argmin(y))
                    else:
                        peak_idx = int(np.argmax(y))

                peak_x = x[peak_idx]
                span = float(max(x) - min(x))
                plt.xlim(peak_x - span / 2, peak_x + span / 2)

            plt.plot(x, y, color=self.curve_color, linewidth=self.line_width)

            # 设置坐标轴粗细
            for spine in ax.spines.values():
                spine.set_linewidth(self.axis_width)

            xlabel = self.heads.get(2, "Temperature")
            ylabel = self.heads.get(3, "Heat Flow")

            font1 = {
                "size": self.axis_font_size,
                "weight": "bold",
                "fontname": "Arial",
            }
            plt.xlabel(xlabel, labelpad=4, fontdict=font1)
            plt.ylabel(ylabel, labelpad=4, fontdict=font1)
            plt.xticks(weight="bold")
            plt.yticks(weight="bold")

            pic_subdir = os.path.join(
                self.pic_dir, os.path.splitext(self.filename)[0]
            )
            if not os.path.exists(pic_subdir):
                os.makedirs(pic_subdir, exist_ok=True)

            plt.savefig(
                os.path.join(pic_subdir, f"Cycle {num + 1}.png"),
                transparent=self.transparent_back,
            )
            plt.close(fig)

    def cycle_draw(self) -> List[plt.Figure]:
        """绘制循环叠加图

        Returns:
            A list of matplotlib *Figure* objects (one per cycle directory)
            so that callers / the frontend can display them as needed.
        """
        cycle_list = glob.glob(os.path.join(self.cycle_dir, "Cycle*"))
        figures: List[plt.Figure] = []

        for pro, cycle_path in enumerate(cycle_list):
            plt.cla()
            fig = plt.figure(dpi=300, figsize=(16, 8))
            labels: List[str] = []

            csv_files = glob.glob(os.path.join(cycle_path, "*.csv"))

            # 用于计算平均峰位置
            peak_x_list: List[float] = []
            all_x_min: List[float] = []
            all_x_max: List[float] = []

            for num, file in enumerate(csv_files):
                try:
                    data = np.loadtxt(file, delimiter=",")
                    name = os.path.splitext(os.path.basename(file))[0]

                    x = data[:, 0]
                    y = data[:, 1]

                    if len(x) <= 1:
                        continue

                    # 如果勾选了峰始终向上
                    if self.peaks_upward:
                        if x[-1] > x[0]:
                            y = -y

                    # 收集峰位置信息用于居中
                    if self.center_peak:
                        peak_idx: int = 0
                        if self.peaks_upward:
                            peak_idx = int(np.argmax(y))
                        else:
                            y_centered = y - np.median(y)
                            if np.abs(np.min(y_centered)) > np.abs(
                                np.max(y_centered)
                            ):
                                peak_idx = int(np.argmin(y))
                            else:
                                peak_idx = int(np.argmax(y))
                        peak_x_list.append(float(x[peak_idx]))
                        all_x_min.append(float(min(x)))
                        all_x_max.append(float(max(x)))

                    color_idx = num % len(self.color_list)
                    plt.plot(x, y, c=self.color_list[color_idx], label=name)
                    labels.append(name)
                except Exception as e:
                    self.logger.warning(f"读取CSV失败 {file}: {e}")

            # 应用峰居中
            if self.center_peak and peak_x_list:
                avg_peak_x = float(np.mean(peak_x_list))
                if all_x_min and all_x_max:
                    avg_span = float(
                        np.mean(np.array(all_x_max) - np.array(all_x_min))
                    )
                    plt.xlim(avg_peak_x - avg_span / 2, avg_peak_x + avg_span / 2)

            if labels:
                plt.legend(labels)

            if self.save_cycle_pic:
                plt.savefig(os.path.join(cycle_path, "result.png"))

            # 进度更新
            if self.progress_callback:
                self.progress_callback(
                    (pro + 1) / len(cycle_list),
                    "画图进度 {}/{} {:.2f}%".format(
                        pro + 1, len(cycle_list), (pro + 1) * 100 / len(cycle_list)
                    ),
                )

            figures.append(fig)

            # Close figure if caller does not need to display it
            if not self.display_pic:
                plt.close(fig)

        return figures

    # -- main entry point --------------------------------------------------

    def run(self) -> bool:
        """运行DSC分析"""
        self.clear_dir()
        if self.info_callback:
            self.info_callback("处理原数据...")

        file_list = glob.glob(os.path.join(self.data_path, "*.txt"))
        if not file_list:
            self.logger.warning("数据文件夹中没有相应文件", show_ui=True)
            return False

        for pro, file_path in enumerate(file_list):
            filename = os.path.basename(file_path)
            if self.read_file(filename):
                if self.info_callback:
                    self.info_callback(f"预处理文件: {filename}...")
                self.preprocess()

                if self.info_callback:
                    self.info_callback(f"数据切片: {filename}...")

                if self.save_seg_mode:
                    if self.info_callback:
                        self.info_callback(f"保存切片数据: {filename}...")
                    self.save_data_seg()

                if self.draw_seg_mode:
                    if self.info_callback:
                        self.info_callback(f"分循环做图: {filename}...")
                    self.draw_img()

            if self.progress_callback:
                self.progress_callback(
                    (pro + 1) / len(file_list),
                    "处理进度 {}/{} {:.2f}%".format(
                        pro + 1,
                        len(file_list),
                        (pro + 1) * 100 / len(file_list),
                    ),
                )

        if self.draw_cycle:
            if self.info_callback:
                self.info_callback("绘制各循环叠加图...")
            self.cycle_draw()

        return True
