"""
GPCAnalyzer — GPC (Gel Permeation Chromatography) analysis module.

Extracted from the monolithic main.py for the v2 refactoring.
All Streamlit dependencies have been removed; UI display is handled by the frontend.
"""

import os
import glob
import numpy as np
import pandas as pd
from typing import List, Optional, Callable

from .base import (
    BaseAnalyzer,
    FIGURE_DPI,
    GPC_FIGURE_SIZE,
    MW_DATA_OFFSET,
    GPC_X_COLUMN_INDEX,
    GPC_Y_COLUMN_INDEX,
    MIN_GPC_PEAK_COLUMNS,
)


class GPCAnalyzer(BaseAnalyzer):
    """GPC 分析器 — 处理 GPC 数据文件、绘制叠加色谱图、输出分子量汇总。"""

    def __init__(
        self,
        datadir: str,
        output_filename: str,
        save_file: bool = True,
        save_picture: bool = True,
        display_mode: bool = True,
        save_figure_file_gpc: bool = True,
        test_mode: bool = False,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        info_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(datadir, test_mode=test_mode,
                         progress_callback=progress_callback,
                         info_callback=info_callback)
        self.output_dir: str = os.path.join(os.path.dirname(self.data_path), "GPC_output")
        self.file_list: Optional[List[str]] = None
        self.output_filename: str = output_filename
        self.selected_file: Optional[List[str]] = None

        # 运行模式
        self.save_file: bool = save_file
        self.save_picture: bool = save_picture
        self.display_mode: bool = display_mode
        self.save_figure_file_gpc: bool = save_figure_file_gpc

        # 画图颜色库
        from .cnames import clist
        self.color_list: list = clist

    # ------------------------------------------------------------------
    # Directory helpers
    # ------------------------------------------------------------------

    def clear_dir(self) -> None:
        """清空输出目录"""
        super().clear_dir(self.output_dir)

    def check_dir(self) -> bool:
        """检查输出目录中是否存在同名文件

        Returns:
            bool: 存在同名文件返回 True
        """
        csv_path = os.path.join(self.output_dir, self.output_filename + ".csv")
        png_path = os.path.join(self.output_dir, self.output_filename + ".png")
        return os.path.exists(csv_path) or os.path.exists(png_path)

    # ------------------------------------------------------------------
    # Data preprocessing
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
        all_peaks: list = []
        for line in self.lines[slice_table_start + 1:]:
            if ("Peak" in line and len(current_peak) > 1) or "</Slice_Table>" in line:
                try:
                    peak_array = np.array(current_peak[1:], dtype="float")
                    if (peak_array.shape[0] > 0
                            and peak_array.shape[1] > MIN_GPC_PEAK_COLUMNS):
                        all_peaks.append(peak_array)
                    else:
                        self.logger.warning(
                            f"文件 {self.filename}: 峰数据格式不正确，跳过该峰"
                        )
                except (ValueError, IndexError) as e:
                    self.logger.warning(
                        f"文件 {self.filename}: 峰数据转换失败: {e}"
                    )
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

        self.peak_data[self.sample_name] = all_peaks

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_image(self) -> None:
        """绘制 GPC 叠加色谱图并保存到文件"""
        import matplotlib.pyplot as plt

        if not self.peak_data:
            raise ValueError("没有可用的峰数据用于绘图")

        fig = None
        try:
            fig = plt.figure(dpi=FIGURE_DPI, figsize=GPC_FIGURE_SIZE)
            plotted_labels: List[str] = []
            for sample_idx, (sample_name, peak_data_list) in enumerate(
                self.peak_data.items()
            ):
                if sample_idx >= len(self.color_list):
                    self.logger.warning(f"颜色库不足，跳过样品 {sample_name}")
                    break
                for peak_array in peak_data_list:
                    if peak_array.shape[1] <= MIN_GPC_PEAK_COLUMNS:
                        self.logger.warning(
                            f"样品 {sample_name} 的峰数据不完整，跳过"
                        )
                        continue
                    x_data = peak_array[:, GPC_X_COLUMN_INDEX]
                    y_data = peak_array[:, GPC_Y_COLUMN_INDEX]
                    plt.plot(
                        x_data, y_data,
                        c=self.color_list[sample_idx],
                        label=sample_name,
                    )
                    plotted_labels.append(sample_name)

            if not plotted_labels:
                raise ValueError("没有有效数据可以绘图")

            plt.legend(plotted_labels)
            result_name = self.output_filename
            os.makedirs(self.output_dir, exist_ok=True)
            if self.save_picture:
                plt.savefig(os.path.join(self.output_dir, result_name + ".png"))
            # Display is handled by the frontend — no st.pyplot call.
        finally:
            if fig is not None:
                plt.close(fig)

    # ------------------------------------------------------------------
    # Data output
    # ------------------------------------------------------------------

    def output_data(self) -> None:
        """将分子量汇总数据输出为 CSV 文件"""
        column = ["Samplename", "Mp", "Mn", "Mw", "Mz", "Mz+1", "Mv", "PD"]
        result_name = self.output_filename
        data = pd.DataFrame(data=self.mw_data, columns=column)
        os.makedirs(self.output_dir, exist_ok=True)
        if self.save_file:
            data.to_csv(os.path.join(self.output_dir, result_name + ".csv"))

    def output_figure_data(self) -> None:
        """将色谱图数据输出为 Excel 文件"""
        result_name = os.path.join(self.output_dir, self.output_filename + ".xlsx")
        os.makedirs(self.output_dir, exist_ok=True)
        xlsx = pd.ExcelWriter(result_name, engine="openpyxl")
        for _num, (name, data) in enumerate(self.peak_data.items()):
            for peak in data:
                df = pd.DataFrame(peak[:, 5:7])
                df.to_excel(xlsx, sheet_name=name, index=False, header=False)
        xlsx.close()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self) -> bool:
        """运行 GPC 分析流程

        Returns:
            bool: 成功返回 True，失败返回 False
        """
        if self.selected_file is None:
            self.file_list = [
                os.path.basename(i)
                for i in glob.glob(os.path.join(self.data_path, "*.rst"))
            ]
        else:
            self.file_list = self.selected_file

        # 在开始处理前清空 peak_data，确保不会累积旧数据
        self.peak_data = {}

        for pro, filename in enumerate(self.file_list):
            self.filename = filename
            try:
                if self.read_file(filename, reset_peak_data=False):
                    self.preprocess()
                    self.logger.info(f"成功处理文件: {filename}")
            except Exception as e:
                self.logger.error(
                    f"处理文件 {filename} 时出错", show_ui=True, exception=e
                )
            finally:
                if self.progress_callback:
                    total = len(self.file_list)
                    pct = (pro + 1) * 100 / total
                    self.progress_callback(
                        (pro + 1) / total,
                        f"画图进度 {pro + 1}/{total} {pct:.2f}%",
                    )

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
