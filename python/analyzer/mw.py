"""
MolecularWeightAnalyzer — molecular-weight distribution analysis.

Extracted from the monolithic main.py for the v2 refactoring.
All Streamlit dependencies have been removed; UI display is handled externally.
"""

import os
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .base import (
    BaseAnalyzer,
    SettingsManager,
    DEFAULT_BAR_COLOR,
    DEFAULT_MW_COLOR,
    DEFAULT_SETTING_NAME,
    DEFAULT_TRANSPARENT_BACK,
    FIGURE_DPI,
    FIGURE_SIZE_WITH_TABLE,
    FIGURE_SIZE_WITHOUT_TABLE,
    GRIDSPEC_ROWS,
    GRIDSPEC_COLS,
    MW_DATA_OFFSET,
    NORM_COLUMN_INDEX,
    MW_COLUMN_INDEX,
    MIN_PEAK_COLUMNS,
    MIN_MW_DATA_COLUMNS,
    NORM_SCALE_FACTOR,
    PERCENTAGE_FACTOR,
    BAR_POSITION_WEIGHT_LEFT,
    BAR_POSITION_WEIGHT_RIGHT,
)


class MolecularWeightAnalyzer(BaseAnalyzer):
    """分子量分布分析器 — 读取 .rst 文件并生成 Mw 分布图。"""

    def __init__(
        self,
        datadir: str,
        save_file: bool = True,
        bar_width: float = 1.2,
        line_width: float = 1.0,
        axis_width: float = 1.0,
        title_font_size: float = 20,
        axis_font_size: float = 14,
        transparent_back: bool = DEFAULT_TRANSPARENT_BACK,
        save_picture: bool = True,
        display_picture: bool = False,
        bar_color: str = DEFAULT_BAR_COLOR,
        mw_color: str = DEFAULT_MW_COLOR,
        draw_bar: bool = True,
        draw_mw: bool = True,
        draw_table: bool = True,
        setting_name: str = DEFAULT_SETTING_NAME,
        test_mode: bool = False,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> None:
        super().__init__(datadir, test_mode=test_mode, progress_callback=progress_callback)
        self.output_dir: str = os.path.join(os.path.dirname(self.data_path), "Mw_output")
        self.setting_dir: str = os.path.join(self.rootdir, "setting")
        self.file_list: Optional[List[str]] = None
        self.selected_file: Optional[List[str]] = None

        # Per-file data
        self.norm: Optional[np.ndarray] = None
        self.mw: Optional[np.ndarray] = None

        # Settings manager
        default_setting: Dict[str, Any] = {
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
        self.settings_manager = SettingsManager(self.setting_dir, setting_name, default_setting)

        # Load persisted settings
        self.setting_name: str = setting_name
        setting = self.settings_manager.load_setting(self.setting_name)

        # Plot attributes
        self.bar_color: str = setting.get("bar_color", DEFAULT_BAR_COLOR)
        self.mw_color: str = setting.get("mw_color", DEFAULT_MW_COLOR)
        self.transparent_back: bool = setting.get("transparent_back", DEFAULT_TRANSPARENT_BACK)
        self.bar_width: float = setting.get("bar_width", 1.2)
        self.line_width: float = setting.get("line_width", 1.0)
        self.axis_width: float = setting.get("axis_width", 1.0)
        self.title_font_size: float = setting.get("title_font_size", 20)
        self.axis_font_size: float = setting.get("axis_font_size", 14)
        self.draw_bar: bool = setting.get("draw_bar", True)
        self.draw_mw: bool = setting.get("draw_mw", True)
        self.draw_table: bool = setting.get("draw_table", True)

        # Segment positions
        self.segmentpos: List[int] = setting.get(
            "segmentpos",
            [0, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000, 10000000, 50000000],
        )
        self.selectedpos: List[int] = list(self.segmentpos)
        self.segmentnum: int = len(self.segmentpos)

        # Run-mode flags
        self.test_mode: bool = test_mode
        self.save_file: bool = save_file
        self.save_picture: bool = save_picture
        self.display_picture: bool = display_picture

    # ------------------------------------------------------------------
    # Directory helpers
    # ------------------------------------------------------------------

    def clear_dir(self) -> None:  # type: ignore[override]
        """清空输出目录"""
        super().clear_dir(self.output_dir)

    def check_dir(self) -> bool:
        """检查输出目录中是否存在同名文件"""
        if not self.selected_file:
            return False
        for file in self.selected_file:
            if os.path.exists(os.path.join(self.output_dir, os.path.splitext(file)[0] + ".png")):
                return True
        return False

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def setting_list(self) -> List[str]:
        """获取所有设置文件列表"""
        return self.settings_manager.list_settings()

    def save_setting(self, new_setting_name: str = "") -> None:
        """保存当前设置到文件"""
        setting: Dict[str, Any] = {
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
            "draw_table": self.draw_table,
        }
        self.settings_manager.save_setting(setting, new_setting_name)

    def delete_setting(self, settingname: str) -> None:
        """删除指定的设置文件"""
        self.settings_manager.delete_setting(settingname)

    def change_setting(self, settingname: str) -> None:
        """切换到指定的设置"""
        self.setting_name = settingname

    # ------------------------------------------------------------------
    # Region management
    # ------------------------------------------------------------------

    def add_region(self, new_region: int) -> None:
        """添加新的分子量区间分割点"""
        self.segmentpos.append(new_region)
        self.segmentpos.sort()

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    def read_file(self, name: str) -> bool:
        """读取数据文件"""
        self.reset()
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
            self.logger.error(f"文件编码错误: {name}，请确保文件为ASCII编码", show_ui=True)
            return False
        except Exception as e:
            self.logger.error(f"读取文件失败 {name}", show_ui=True, exception=e)
            return False

    # ------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------

    def preprocess(self) -> None:
        """预处理数据文件，提取分子量和峰数据"""
        mw_start, mw_end, slice_table_start = self.preprocess_common()

        # 整理分子量数据
        for line in self.lines[mw_start + MW_DATA_OFFSET:mw_end]:
            parts = line.split("\t")
            if len(parts) > 1:
                self.mw_data.append([self.sample_name] + parts[1:])

        if not self.mw_data:
            raise ValueError("未找到分子量数据")

        self.peak_num = len(self.mw_data)

        # 提取峰数据
        current_peak: List[List[str]] = []
        all_peaks: List[np.ndarray] = []
        for line in self.lines[slice_table_start + 1:]:
            if ("Peak" in line and len(current_peak) > 1) or "</Slice_Table>" in line:
                try:
                    peak_array = np.array(current_peak[1:], dtype="float")
                    if peak_array.shape[0] > 0 and peak_array.shape[1] > MIN_PEAK_COLUMNS:
                        self.norm = peak_array[:, NORM_COLUMN_INDEX]
                        self.mw = peak_array[:, MW_COLUMN_INDEX]
                        all_peaks.append(peak_array)
                    else:
                        self.logger.warning("峰数据格式不正确，跳过该峰")
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"峰数据转换失败: {e}")
                current_peak = []
                continue
            if "RT" in line:
                continue
            line_parts = line.split("\t")[:-1]
            if line_parts and "-2" in line_parts[0]:
                continue
            current_peak.append(line_parts)

        if not all_peaks:
            raise ValueError("未找到有效的峰数据")

        self.peak_data = all_peaks

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def transform_number(num: float) -> str:
        """将数字转换为科学记数法格式"""
        dig = len(str(num)) - 1
        front = num / (10 ** dig)
        return "{:.1f} × 10$^{}$".format(front, dig)

    def start_width(self) -> int:
        """计算起始宽度"""
        return (len(str(self.segmentpos[1])) - 2) * 2

    # ------------------------------------------------------------------
    # Drawing internals
    # ------------------------------------------------------------------

    def _validate_draw_data(self) -> None:
        """验证绘图所需的数据完整性"""
        if not self.validator.validate_data_not_empty(self.norm, "归一化数据"):
            raise ValueError(f"文件 {self.filename}: 没有可用的归一化数据")
        if not self.validator.validate_data_not_empty(self.mw, "分子量数据"):
            raise ValueError(f"文件 {self.filename}: 没有可用的分子量数据")
        if not self.validator.validate_segment_positions(self.selectedpos):
            raise ValueError("至少需要2个分割位置")

    def _calculate_segment_percentages(self) -> List[float]:
        """计算各分子量区间的百分比"""
        segment_percentages: List[float] = []
        for segment_idx in range(len(self.selectedpos) - 1):
            lower_bound = self.selectedpos[segment_idx]
            upper_bound = self.selectedpos[segment_idx + 1]
            mask = (self.mw < upper_bound) & (self.mw > lower_bound)
            segment_sum = float(np.sum(self.norm[np.where(mask)]) * PERCENTAGE_FACTOR)
            segment_percentages.append(segment_sum)
        self.logger.debug(f"计算区间百分比: {segment_percentages}")
        return segment_percentages

    def _setup_figure(self) -> Tuple[Any, Any, Any]:
        """设置并创建图形对象

        Returns:
            (fig, ax, gs)
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
        """绘制分子量分布曲线和柱状图"""
        import matplotlib.pyplot as plt

        # Bar positions & widths
        bar_positions = [
            (self.selectedpos[idx] * BAR_POSITION_WEIGHT_LEFT
             + self.selectedpos[idx + 1] * BAR_POSITION_WEIGHT_RIGHT)
            for idx in range(len(self.selectedpos) - 1)
        ]
        bar_widths = [pos * self.bar_width for pos in bar_positions]

        # Normalise
        max_norm = max(self.norm)
        if max_norm > 0:
            normalized_data = [value * NORM_SCALE_FACTOR / max_norm for value in self.norm]
        else:
            normalized_data = [0] * len(self.norm)
            self.logger.warning(f"文件 {self.filename}: 归一化数据最大值为0")

        # Axis spine width
        for spine in ax.spines.values():
            spine.set_linewidth(self.axis_width)

        # Curves & bars
        if self.draw_mw:
            ax.plot(self.mw, normalized_data, color=self.mw_color, linewidth=self.line_width)
        if self.draw_bar:
            ax.bar(bar_positions, segment_percentages, align="edge", width=bar_widths, color=self.bar_color)

        # Style
        plt.xscale("log")
        font1: Dict[str, Any] = {"size": self.axis_font_size, "weight": "bold", "fontname": "Arial"}
        font2: Dict[str, Any] = {"size": self.title_font_size, "weight": "bold", "fontname": "Arial"}
        plt.xlabel("Mw (g /mol)", labelpad=4, fontdict=font1)
        plt.ylabel("Cumulative%", labelpad=4, fontdict=font1)
        plt.xticks(weight="bold")
        plt.yticks(weight="bold")

        result_name = self.filename.split(".")[0]
        plt.title(result_name, pad=10, fontdict=font2)

    def _create_distribution_table(self, fig: Any, gs: Any, segment_percentages: List[float]) -> None:
        """创建分子量区间分布表格"""
        from plottable import ColumnDefinition, Table

        ax1 = fig.add_subplot(gs[:6, 5:7])
        distribution_data: List[List[str]] = []

        for segment_idx, _pos in enumerate(self.selectedpos[1:-1]):
            if segment_idx == 0:
                range_label = "< " + self.transform_number(self.selectedpos[segment_idx + 1])
            elif segment_idx == len(self.selectedpos[1:-1]) - 1:
                range_label = ">" + self.transform_number(self.selectedpos[segment_idx])
            else:
                range_label = (
                    self.transform_number(self.selectedpos[segment_idx])
                    + " ~ "
                    + self.transform_number(self.selectedpos[segment_idx + 1])
                )
            percentage_text = "{:.2f}%".format(segment_percentages[segment_idx])
            distribution_data.append([range_label, percentage_text])

        df_distribution = pd.DataFrame(data=distribution_data, columns=["Mw", "Percent"]).set_index("Mw")
        Table(
            df_distribution,
            ax=ax1,
            textprops={"fontsize": 12, "fontname": "Times New Roman"},
            column_definitions=[
                ColumnDefinition(name="Mw", width=10, textprops={"ha": "center"}),
                ColumnDefinition(name="Percent", width=4, textprops={"ha": "center"}),
            ],
            footer_divider=True,
            row_dividers=True,
        )

    def _create_stats_table(self, fig: Any, gs: Any) -> None:
        """创建分子量统计数据表格"""
        from plottable import ColumnDefinition, Table

        stats_data: List[List[str]] = []
        ax2 = fig.add_subplot(gs[7, 5:7])

        if (
            self.mw_data
            and len(self.mw_data) > 0
            and self.validator.validate_array_shape(
                np.array(self.mw_data), min_rows=1, min_cols=MIN_MW_DATA_COLUMNS, name="分子量数据"
            )
        ):
            for mw_row in self.mw_data:
                if len(mw_row) >= MIN_MW_DATA_COLUMNS:
                    # index 2=Mn, 3=Mw, 7=PDI
                    stats_data.append([self.mw_data[0][2], self.mw_data[0][3], self.mw_data[0][7]])
                else:
                    self.logger.warning("分子量数据不完整，跳过表格生成", show_ui=True)
                    break
        else:
            self.logger.warning("分子量数据格式错误，跳过表格生成", show_ui=True)

        if stats_data:
            df_stats = pd.DataFrame(data=stats_data, columns=["Mn", "Mw", "PDI"]).set_index("Mn")
            Table(
                df_stats,
                ax=ax2,
                textprops={"fontsize": 12, "fontname": "Times New Roman"},
                column_definitions=[
                    ColumnDefinition(name="Mw", textprops={"ha": "center"}),
                    ColumnDefinition(name="Mn", textprops={"ha": "center"}),
                    ColumnDefinition(name="PDI", textprops={"ha": "center"}),
                ],
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def draw_image(self) -> None:
        """绘制分子量分布图"""
        import matplotlib.pyplot as plt

        self._validate_draw_data()
        segment_percentages = self._calculate_segment_percentages()

        fig = None
        try:
            fig, ax, gs = self._setup_figure()
            self._plot_data(ax, segment_percentages)

            if self.draw_table:
                self._create_distribution_table(fig, gs, segment_percentages)
                self._create_stats_table(fig, gs)

            # Save
            result_name = os.path.splitext(self.filename)[0]
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, exist_ok=True)
            if self.save_picture:
                plt.savefig(
                    os.path.join(self.output_dir, result_name + ".png"),
                    transparent=self.transparent_back,
                )
                self.logger.debug(f"已保存图片: {result_name}.png")
        finally:
            if fig is not None:
                plt.close(fig)

    def output_data(self) -> None:
        """输出数据（占位）"""
        _column = ["Samplename", "Mp", "Mn", "Mw", "Mz", "Mz+1", "Mv", "PD"]

    def run(self) -> bool:
        """运行分析流程 — 处理所有选中的文件，生成分子量分布图"""
        if not self.selected_file:
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
                continue
            finally:
                if self.progress_callback:
                    self.progress_callback(
                        (pro + 1) / len(self.file_list),
                        "画图进度 {}/{} {:.2f}%".format(
                            pro + 1, len(self.file_list), (pro + 1) * 100 / len(self.file_list)
                        ),
                    )

        return True
