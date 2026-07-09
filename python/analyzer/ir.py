"""IR DPT analyzer — parse .dpt spectra and generate plots."""

from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime
from typing import Any, Callable, List, Optional

import numpy as np

from .base import (
    BaseAnalyzer,
    DEFAULT_BAR_COLOR,
    DEFAULT_TRANSPARENT_BACK,
    FIGURE_DPI,
    get_install_dir,
)
from .plotting import configure_plotting

GAPS: tuple[tuple[float, float], ...] = ((2800, 3000), (1380, 1460))


class IRAnalyzer(BaseAnalyzer):
    """Analyze .dpt infrared spectra and save PNG outputs."""

    def __init__(
        self,
        datadir: str,
        selected_files: Optional[List[str]] = None,
        curve_color: str = DEFAULT_BAR_COLOR,
        line_width: float = 1.0,
        axis_width: float = 1.0,
        title_font_size: int = 20,
        axis_font_size: int = 14,
        transparent_back: bool = DEFAULT_TRANSPARENT_BACK,
        normalize_overlay: bool = True,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> None:
        super().__init__(datadir=datadir, progress_callback=progress_callback)
        self.output_dir = os.path.join(get_install_dir(), "IR_output")
        self.individual_dir = os.path.join(self.output_dir, "individual")
        self.selected_files = selected_files
        self.curve_color = curve_color
        self.line_width = line_width
        self.axis_width = axis_width
        self.title_font_size = title_font_size
        self.axis_font_size = axis_font_size
        self.transparent_back = transparent_back
        self.normalize_overlay = normalize_overlay

    def read_file_list(self, force_refresh: bool = False) -> List[str]:  # type: ignore[override]
        if self._cached_file_list is None or force_refresh:
            if not os.path.isdir(self.data_path):
                self._cached_file_list = []
            else:
                self._cached_file_list = sorted(
                    [
                        name
                        for name in os.listdir(self.data_path)
                        if name.lower().endswith(".dpt")
                    ],
                    key=str.lower,
                )
        return self._cached_file_list

    def run(self) -> bool:
        files = self.selected_files if self.selected_files is not None else self.read_file_list()
        if not files:
            raise ValueError("No .dpt files selected")

        self._emit_progress(0.01, "Preparing IR plot engine")
        plt = configure_plotting()
        self._prepare_output_dir()
        generated: list[str] = []
        spectra: list[dict[str, Any]] = []
        total = len(files)
        work_start = 0.08
        work_span = 0.82

        for index, filename in enumerate(files, start=1):
            if not filename.lower().endswith(".dpt"):
                continue
            self._emit_progress(
                work_start + work_span * ((index - 1) / max(total, 1)),
                f"Reading {filename}",
            )
            wn, absorbance = self.parse_dpt(os.path.join(self.data_path, filename))
            if wn.size == 0:
                self.logger.warning(f"未找到有效 DPT 数据: {filename}")
                continue

            transmittance = self.absorbance_to_transmittance(absorbance)
            sample_name = os.path.splitext(os.path.basename(filename))[0]
            output_path = os.path.join(self.individual_dir, f"{sample_name}.png")
            self.plot_spectrum(plt, wn, transmittance, sample_name, output_path)
            generated.append(output_path)
            spectra.append({"name": sample_name, "wavenumber": wn, "transmittance": transmittance})
            self._emit_progress(
                work_start + work_span * (index / max(total, 1)),
                f"Plotted {filename}",
            )

        if not spectra:
            raise ValueError("No valid .dpt spectra found")

        self._emit_progress(0.92, "Plotting overlay")
        overlay_path = os.path.join(self.output_dir, "dpt_overlay.png")
        self.plot_overlay(plt, spectra, overlay_path)
        generated.append(overlay_path)

        manifest_path = self.write_manifest(files, generated)
        generated.append(manifest_path)
        self.generated_files = generated
        self.processed_count = len(spectra)
        self._emit_progress(1.0, f"Generated {len(generated)} files")
        return True

    def _prepare_output_dir(self) -> None:
        if os.path.isdir(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.individual_dir, exist_ok=True)

    def _emit_progress(self, progress: float, message: str) -> None:
        if self.progress_callback:
            self.progress_callback(progress, message)

    @staticmethod
    def parse_dpt(filepath: str) -> tuple[np.ndarray, np.ndarray]:
        rows: list[tuple[float, float]] = []
        splitter = re.compile(r"[\s,;]+")
        with open(filepath, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                parts = [part for part in splitter.split(line.strip()) if part]
                if len(parts) < 2:
                    continue
                try:
                    rows.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    continue

        if not rows:
            return np.array([], dtype=float), np.array([], dtype=float)

        data = np.array(rows, dtype=float)
        return data[:, 0], data[:, 1]

    @staticmethod
    def absorbance_to_transmittance(absorbance: np.ndarray) -> np.ndarray:
        absorbance_clamped = np.clip(absorbance, None, 1.99)
        return 10.0 ** (2.0 - absorbance_clamped)

    @staticmethod
    def normalize_to_baseline(wavenumber: np.ndarray, transmittance: np.ndarray) -> np.ndarray:
        mask = (wavenumber >= 1750) & (wavenumber <= 1850)
        if not mask.any():
            return transmittance
        baseline_max = np.max(transmittance[mask])
        if baseline_max <= 0:
            return transmittance
        return transmittance / baseline_max * 100.0

    def plot_spectrum(
        self,
        plt: Any,
        wavenumber: np.ndarray,
        transmittance: np.ndarray,
        title: str,
        output_path: str,
    ) -> None:
        fig, ax = plt.subplots(figsize=(12, 5))
        fig.patch.set_facecolor("white")
        self._plot_with_gaps(ax, wavenumber, transmittance, color=self.curve_color, label=title)
        self._style_axis(ax, title)
        fig.tight_layout()
        fig.savefig(
            output_path,
            dpi=FIGURE_DPI,
            facecolor="none" if self.transparent_back else "white",
            transparent=self.transparent_back,
        )
        plt.close(fig)

    def plot_overlay(self, plt: Any, spectra: list[dict[str, Any]], output_path: str) -> None:
        fig, ax = plt.subplots(figsize=(14, 6))
        fig.patch.set_facecolor("white")
        colors = plt.cm.tab10(np.linspace(0, 1, max(len(spectra), 3)))

        for spectrum, color in zip(spectra, colors):
            wavenumber = spectrum["wavenumber"]
            transmittance = spectrum["transmittance"]
            if self.normalize_overlay:
                transmittance = self.normalize_to_baseline(wavenumber, transmittance)
            self._plot_with_gaps(
                ax,
                wavenumber,
                transmittance,
                color=color,
                label=spectrum["name"],
            )

        self._style_axis(ax, "红外光谱对比 (DPT 样品)")
        ax.legend(loc="lower right", framealpha=0.9, fontsize=11, edgecolor="gray", fancybox=False)
        fig.tight_layout()
        fig.savefig(
            output_path,
            dpi=FIGURE_DPI,
            facecolor="none" if self.transparent_back else "white",
            transparent=self.transparent_back,
        )
        plt.close(fig)

    def _plot_with_gaps(
        self,
        ax: Any,
        wavenumber: np.ndarray,
        transmittance: np.ndarray,
        *,
        color: Any,
        label: str,
    ) -> None:
        x = wavenumber.astype(float).copy()
        y = transmittance.astype(float).copy()
        gap_mask = np.zeros_like(x, dtype=bool)

        for start, end in GAPS:
            low, high = sorted((start, end))
            gap_mask |= (x >= low) & (x <= high)

            below = np.where(x < low)[0]
            above = np.where(x > high)[0]
            if below.size and above.size:
                below_idx = below[np.argmax(x[below])]
                above_idx = above[np.argmin(x[above])]
                ax.plot(
                    [x[above_idx], x[below_idx]],
                    [y[above_idx], y[below_idx]],
                    color=color,
                    linewidth=self.line_width * 0.85,
                    linestyle=(0, (5, 5)),
                    alpha=0.75,
                )

        y[gap_mask] = np.nan
        ax.plot(x, y, color=color, linewidth=self.line_width, label=label)

    def _style_axis(self, ax: Any, title: str) -> None:
        ax.set_xlim(4000, 400)
        ax.set_xlabel("波数 (cm$^{-1}$)", fontsize=self.axis_font_size)
        ax.set_ylabel("透过率 (%)", fontsize=self.axis_font_size)
        ax.set_title(title, fontsize=self.title_font_size)
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.tick_params(direction="in", which="both", top=True, right=True, width=self.axis_width)
        for spine in ax.spines.values():
            spine.set_linewidth(self.axis_width)

    def write_manifest(self, input_files: list[str], generated_files: list[str]) -> str:
        manifest_path = os.path.join(self.output_dir, "manifest.json")
        manifest = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "input_dir": self.data_path,
            "output_dir": self.output_dir,
            "input_files": input_files,
            "generated_files": [
                os.path.relpath(path, self.output_dir)
                for path in generated_files
            ],
        }
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
        return manifest_path
