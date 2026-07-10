"""IR DPT analyzer — parse .dpt spectra and generate plots."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from typing import Any, Callable, List, Optional

import numpy as np

from .base import (
    BaseAnalyzer,
    DEFAULT_TRANSPARENT_BACK,
    FIGURE_DPI,
    get_install_dir,
    replace_directories_atomically,
    resolve_contained_file,
)
from .plotting import configure_plotting

GAPS: tuple[tuple[float, float], ...] = ((2800, 3000), (1380, 1460))
IR_DEFAULT_CURVE_COLOR = "#D62728"
DEFAULT_NORMALIZATION_PEAK = 1450.0
NORMALIZATION_WINDOW = 80.0
NORMALIZATION_TARGET_ABSORBANCE = 0.6


class IRAnalyzer(BaseAnalyzer):
    """Analyze .dpt infrared spectra and save PNG outputs."""

    def __init__(
        self,
        datadir: str,
        selected_files: Optional[List[str]] = None,
        curve_color: str = IR_DEFAULT_CURVE_COLOR,
        line_width: float = 1.0,
        axis_width: float = 1.0,
        title_font_size: int = 20,
        axis_font_size: int = 14,
        transparent_back: bool = DEFAULT_TRANSPARENT_BACK,
        draw_overlay: bool = True,
        normalize_overlay: bool = True,
        normalization_peak: float = DEFAULT_NORMALIZATION_PEAK,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> None:
        super().__init__(datadir=datadir, progress_callback=progress_callback)
        if not isinstance(draw_overlay, bool):
            raise ValueError("draw_overlay must be a boolean")
        if not isinstance(normalize_overlay, bool):
            raise ValueError("normalize_overlay must be a boolean")
        if isinstance(normalization_peak, bool):
            raise ValueError("normalization_peak must be a number")
        try:
            normalization_peak_value = float(normalization_peak)
        except (TypeError, ValueError) as exc:
            raise ValueError("normalization_peak must be a number") from exc
        if not np.isfinite(normalization_peak_value) or not 400 <= normalization_peak_value <= 4000:
            raise ValueError("normalization_peak must be between 400 and 4000 cm^-1")

        self.output_dir = os.path.join(get_install_dir(), "IR_output")
        self.individual_dir = os.path.join(self.output_dir, "individual")
        self.selected_files = selected_files
        self.curve_color = curve_color
        self.line_width = line_width
        self.axis_width = axis_width
        self.title_font_size = title_font_size
        self.axis_font_size = axis_font_size
        self.transparent_back = transparent_back
        self.draw_overlay = draw_overlay
        self.normalize_overlay = normalize_overlay
        self.normalization_peak = normalization_peak_value

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
                        and os.path.isfile(os.path.join(self.data_path, name))
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
        output_parent = os.path.dirname(self.output_dir)
        os.makedirs(output_parent, exist_ok=True)
        staging_dir = tempfile.mkdtemp(prefix=".IR_output-staging-", dir=output_parent)
        staging_individual_dir = os.path.join(staging_dir, "individual")
        os.makedirs(staging_individual_dir, exist_ok=True)
        generated: list[str] = []
        spectra: list[dict[str, Any]] = []
        total = len(files)
        work_start = 0.08
        work_span = 0.82

        try:
            for index, filename in enumerate(files, start=1):
                if not isinstance(filename, str) or not filename.lower().endswith(".dpt"):
                    continue
                self._emit_progress(
                    work_start + work_span * ((index - 1) / max(total, 1)),
                    f"Reading {filename}",
                )
                try:
                    input_path = resolve_contained_file(self.data_path, filename)
                    wn, absorbance = self.parse_dpt(input_path)
                    transmittance = self.absorbance_to_transmittance(absorbance)
                except (OSError, ValueError) as exc:
                    self.logger.warning(f"跳过无效 DPT 数据 {filename}: {exc}")
                    continue

                sample_name = os.path.splitext(filename)[0]
                output_path = os.path.join(staging_individual_dir, f"{sample_name}.png")
                self.plot_spectrum(plt, wn, transmittance, sample_name, output_path)
                generated.append(output_path)
                spectra.append({"name": sample_name, "wavenumber": wn, "transmittance": transmittance})
                self._emit_progress(
                    work_start + work_span * (index / max(total, 1)),
                    f"Plotted {filename}",
                )

            if not spectra:
                raise ValueError("No valid .dpt spectra found")

            if self.draw_overlay:
                self._emit_progress(0.92, "Plotting overlay")
                overlay_path = os.path.join(staging_dir, "dpt_overlay.png")
                self.plot_overlay(plt, spectra, overlay_path)
                generated.append(overlay_path)

            manifest_path = self.write_manifest(
                files,
                generated,
                output_dir=staging_dir,
                manifest_output_dir=self.output_dir,
            )
            generated.append(manifest_path)
            relative_generated = [os.path.relpath(path, staging_dir) for path in generated]
            replace_directories_atomically([(staging_dir, self.output_dir)])
        except Exception:
            if os.path.isdir(staging_dir):
                shutil.rmtree(staging_dir, ignore_errors=True)
            raise

        self.generated_files = [os.path.join(self.output_dir, path) for path in relative_generated]
        self.processed_count = len(spectra)
        self._emit_progress(1.0, f"Generated {len(self.generated_files)} files")
        return True

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

        data = np.array(rows, dtype=float)
        if data.shape[0] < 2:
            raise ValueError("DPT data must contain at least two numeric points")
        if not np.isfinite(data).all():
            raise ValueError("DPT data must not contain NaN or infinite values")
        return data[:, 0], data[:, 1]

    @staticmethod
    def absorbance_to_transmittance(absorbance: np.ndarray) -> np.ndarray:
        if not np.isfinite(absorbance).all():
            raise ValueError("Absorbance must not contain NaN or infinite values")
        transmittance = 10.0 ** (2.0 - absorbance)
        if not np.isfinite(transmittance).all():
            raise ValueError("Transmittance calculation produced non-finite values")
        return transmittance

    @staticmethod
    def normalize_to_peak(
        wavenumber: np.ndarray,
        transmittance: np.ndarray,
        *,
        center: float,
        window: float = NORMALIZATION_WINDOW,
        target_absorbance: float = NORMALIZATION_TARGET_ABSORBANCE,
    ) -> np.ndarray:
        """Scale absorbance so the strongest peak near ``center`` reaches a common height."""
        if wavenumber.shape != transmittance.shape or not np.isfinite(wavenumber).all():
            raise ValueError("Wavenumber and transmittance data must be finite and aligned")
        if not np.isfinite(transmittance).all():
            raise ValueError("Transmittance data must be finite")

        mask = (wavenumber >= center - window) & (wavenumber <= center + window)
        if not mask.any():
            raise ValueError(
                f"No spectrum data found near the {center:g} cm^-1 normalization peak"
            )

        absorbance = 2.0 - np.log10(np.clip(transmittance, 0.01, None))
        peak_absorbance = float(np.max(absorbance[mask]))
        if not np.isfinite(peak_absorbance) or peak_absorbance <= 0:
            raise ValueError(
                f"No valid absorbance peak found near {center:g} cm^-1"
            )

        normalized_absorbance = absorbance * (target_absorbance / peak_absorbance)
        normalized = 10.0 ** (2.0 - normalized_absorbance)
        if not np.isfinite(normalized).all():
            raise ValueError("Peak normalization produced non-finite values")
        return normalized

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
        colors: list[Any] = [
            self.curve_color,
            "#1F77B4",
            "#2CA02C",
            "#9467BD",
            "#FF7F0E",
            "#8C564B",
            "#E377C2",
            "#7F7F7F",
            "#BCBD22",
            "#17BECF",
        ]
        if len(spectra) > len(colors):
            colors.extend(
                plt.cm.tab20(np.linspace(0, 1, len(spectra) - len(colors)))
            )

        for spectrum, color in zip(spectra, colors[: len(spectra)]):
            wavenumber = spectrum["wavenumber"]
            transmittance = spectrum["transmittance"]
            if self.normalize_overlay:
                transmittance = self.normalize_to_peak(
                    wavenumber,
                    transmittance,
                    center=self.normalization_peak,
                )
            self._plot_with_gaps(
                ax,
                wavenumber,
                transmittance,
                color=color,
                label=spectrum["name"],
            )

        title = "红外光谱对比 (DPT 样品)"
        if self.normalize_overlay:
            title = f"红外光谱对比 ({self.normalization_peak:g} cm$^{{-1}}$ 峰归一化)"
        self._style_axis(ax, title)
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

    def write_manifest(
        self,
        input_files: list[str],
        generated_files: list[str],
        *,
        output_dir: Optional[str] = None,
        manifest_output_dir: Optional[str] = None,
    ) -> str:
        target_dir = output_dir or self.output_dir
        manifest_path = os.path.join(target_dir, "manifest.json")
        manifest = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "input_dir": self.data_path,
            "output_dir": manifest_output_dir or self.output_dir,
            "input_files": input_files,
            "generated_files": [
                os.path.relpath(path, target_dir)
                for path in generated_files
            ],
            "overlay": {
                "enabled": self.draw_overlay,
                "normalized": self.draw_overlay and self.normalize_overlay,
                "normalization_peak_cm-1": (
                    self.normalization_peak
                    if self.draw_overlay and self.normalize_overlay
                    else None
                ),
            },
        }
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
        return manifest_path
