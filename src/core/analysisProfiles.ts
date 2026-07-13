import type {
  AnalyzerSettings,
  SettingsAnalyzer,
} from "../stores/settingsStore";

const DEFAULT_PROFILE_FILES: Record<SettingsAnalyzer, string> = {
  mw: "defaultSetting.ini",
  dsc: "defaultDSCSetting.ini",
  ir: "defaultIRSetting.ini",
};

export function toProfileFile(analyzer: SettingsAnalyzer, name: string): string {
  if (name === "default") return DEFAULT_PROFILE_FILES[analyzer];
  return name.endsWith(".ini") ? name : `${name}.ini`;
}

export function fromProfileFile(analyzer: SettingsAnalyzer, name: string): string {
  if (name === DEFAULT_PROFILE_FILES[analyzer]) return "default";
  return name.endsWith(".ini") ? name.slice(0, -4) : name;
}

export function toBackendSettings(settings: AnalyzerSettings): Record<string, unknown> {
  return {
    bar_color: settings.barColor,
    mw_color: settings.mwColor,
    curve_color: settings.curveColor,
    transparent_back: settings.transparentBackground,
    draw_bar: settings.drawBar,
    draw_mw: settings.drawMw,
    draw_table: settings.drawTable,
    bar_width: settings.barWidth,
    line_width: settings.lineWidth,
    axis_width: settings.axisWidth,
    title_font_size: settings.titleFontSize,
    axis_font_size: settings.axisFontSize,
    draw_overlay: settings.drawOverlay,
    normalize_overlay: settings.normalizeOverlay,
    normalization_peak: settings.normalizationPeak,
  };
}

export function fromBackendSettings(
  base: AnalyzerSettings,
  value: Record<string, unknown>,
): AnalyzerSettings {
  const number = (key: string, fallback: number) =>
    typeof value[key] === "number" ? value[key] as number : fallback;
  const boolean = (key: string, fallback: boolean) =>
    typeof value[key] === "boolean" ? value[key] as boolean : fallback;
  const string = (key: string, fallback: string) =>
    typeof value[key] === "string" ? value[key] as string : fallback;

  return {
    barColor: string("bar_color", base.barColor),
    mwColor: string("mw_color", base.mwColor),
    curveColor: string("curve_color", base.curveColor),
    transparentBackground: boolean("transparent_back", base.transparentBackground),
    drawBar: boolean("draw_bar", base.drawBar),
    drawMw: boolean("draw_mw", base.drawMw),
    drawTable: boolean("draw_table", base.drawTable),
    barWidth: number("bar_width", base.barWidth),
    lineWidth: number("line_width", base.lineWidth),
    axisWidth: number("axis_width", base.axisWidth),
    titleFontSize: number("title_font_size", base.titleFontSize),
    axisFontSize: number("axis_font_size", base.axisFontSize),
    drawOverlay: boolean("draw_overlay", base.drawOverlay),
    normalizeOverlay: boolean("normalize_overlay", base.normalizeOverlay),
    normalizationPeak: number("normalization_peak", base.normalizationPeak),
  };
}
