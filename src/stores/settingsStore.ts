import { create } from "zustand";
import { persist } from "zustand/middleware";
import i18n from "../i18n";

export type SettingsAnalyzer = "mw" | "dsc" | "ir";

export interface AnalyzerSettings {
  barColor: string;
  mwColor: string;
  curveColor: string;
  transparentBackground: boolean;
  drawBar: boolean;
  drawMw: boolean;
  drawTable: boolean;
  barWidth: number;
  lineWidth: number;
  axisWidth: number;
  titleFontSize: number;
  axisFontSize: number;
  drawOverlay: boolean;
  normalizeOverlay: boolean;
  normalizationPeak: number;
}

export const defaultAnalyzerSettings: AnalyzerSettings = {
  barColor: "#002FA7",
  mwColor: "#FF6A07",
  curveColor: "#002FA7",
  transparentBackground: true,
  drawBar: true,
  drawMw: true,
  drawTable: true,
  barWidth: 1.2,
  lineWidth: 1.0,
  axisWidth: 1.0,
  titleFontSize: 20,
  axisFontSize: 14,
  drawOverlay: true,
  normalizeOverlay: true,
  normalizationPeak: 1450,
};

const defaultIrAnalyzerSettings: AnalyzerSettings = {
  ...defaultAnalyzerSettings,
  curveColor: "#D62728",
};

type AnalyzerSettingsMap = Record<SettingsAnalyzer, AnalyzerSettings>;
type SavedSettingsMap = Record<SettingsAnalyzer, Record<string, AnalyzerSettings>>;

interface SettingsState {
  language: string;
  analyzerSettings: AnalyzerSettingsMap;
  savedSettings: SavedSettingsMap;
  setLanguage: (lang: string) => void;
  updateAnalyzerSettings: (
    analyzer: SettingsAnalyzer,
    patch: Partial<AnalyzerSettings>,
  ) => void;
  saveSettings: (analyzer: SettingsAnalyzer, name: string) => void;
  loadSettings: (analyzer: SettingsAnalyzer, name: string) => void;
  deleteSettings: (analyzer: SettingsAnalyzer, name: string) => void;
  mergeSavedSettings: (
    analyzer: SettingsAnalyzer,
    profiles: Record<string, AnalyzerSettings>,
  ) => void;
}

const ANALYZERS: SettingsAnalyzer[] = ["mw", "dsc", "ir"];

function getDefaultSettings(analyzer: SettingsAnalyzer): AnalyzerSettings {
  return analyzer === "ir"
    ? { ...defaultIrAnalyzerSettings }
    : { ...defaultAnalyzerSettings };
}

function createSettingsMap(): AnalyzerSettingsMap {
  return {
    mw: getDefaultSettings("mw"),
    dsc: getDefaultSettings("dsc"),
    ir: getDefaultSettings("ir"),
  };
}

function createSavedSettingsMap(): SavedSettingsMap {
  return {
    mw: { default: getDefaultSettings("mw") },
    dsc: { default: getDefaultSettings("dsc") },
    ir: { default: getDefaultSettings("ir") },
  };
}

function mergeSettings(
  analyzer: SettingsAnalyzer,
  value: Partial<AnalyzerSettings>,
): AnalyzerSettings {
  const defaults = getDefaultSettings(analyzer);
  const source = value && typeof value === "object" ? value : {};
  const migrated = { ...defaults, ...source };

  // Before overlay settings existed, IR inherited the shared blue curve default.
  if (analyzer === "ir" && !("drawOverlay" in source)) {
    migrated.curveColor = defaults.curveColor;
  }
  return migrated;
}

function hasAnalyzerKeys(value: unknown): value is Record<SettingsAnalyzer, unknown> {
  return Boolean(
    value
      && typeof value === "object"
      && ANALYZERS.every((analyzer) => analyzer in value),
  );
}

function normalizeAnalyzerSettings(value: unknown): AnalyzerSettingsMap {
  const defaults = createSettingsMap();
  if (hasAnalyzerKeys(value)) {
    ANALYZERS.forEach((analyzer) => {
      defaults[analyzer] = mergeSettings(
        analyzer,
        value[analyzer] as Partial<AnalyzerSettings>,
      );
    });
    return defaults;
  }

  if (value && typeof value === "object") {
    const legacy = value as Partial<AnalyzerSettings>;
    ANALYZERS.forEach((analyzer) => {
      defaults[analyzer] = mergeSettings(analyzer, legacy);
    });
  }
  return defaults;
}

function normalizeSavedSettings(value: unknown): SavedSettingsMap {
  const defaults = createSavedSettingsMap();
  const source = hasAnalyzerKeys(value)
    ? value
    : value && typeof value === "object"
      ? { mw: value, dsc: value, ir: value }
      : null;

  if (!source) return defaults;
  ANALYZERS.forEach((analyzer) => {
    const saved = source[analyzer];
    if (!saved || typeof saved !== "object") return;
    Object.entries(saved).forEach(([name, settings]) => {
      if (!settings || typeof settings !== "object") return;
      defaults[analyzer][name] = mergeSettings(
        analyzer,
        settings as Partial<AnalyzerSettings>,
      );
    });
  });
  return defaults;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      language: localStorage.getItem("polyanalyzer-language") || "zh_CN",
      analyzerSettings: createSettingsMap(),
      savedSettings: createSavedSettingsMap(),

      setLanguage: (lang: string) => {
        i18n.changeLanguage(lang);
        localStorage.setItem("polyanalyzer-language", lang);
        set({ language: lang });
      },

      updateAnalyzerSettings: (analyzer, patch) => {
        set((state) => ({
          analyzerSettings: {
            ...state.analyzerSettings,
            [analyzer]: { ...state.analyzerSettings[analyzer], ...patch },
          },
        }));
      },

      saveSettings: (analyzer, name) => {
        set((state) => ({
          savedSettings: {
            ...state.savedSettings,
            [analyzer]: {
              ...state.savedSettings[analyzer],
              [name]: { ...state.analyzerSettings[analyzer] },
            },
          },
        }));
      },

      loadSettings: (analyzer, name) => {
        const saved = get().savedSettings[analyzer][name];
        if (!saved) return;
        set((state) => ({
          analyzerSettings: {
            ...state.analyzerSettings,
            [analyzer]: { ...saved },
          },
        }));
      },

      deleteSettings: (analyzer, name) => {
        if (name === "default") return;
        set((state) => {
          const analyzerSettings = { ...state.savedSettings[analyzer] };
          delete analyzerSettings[name];
          return {
            savedSettings: {
              ...state.savedSettings,
              [analyzer]: analyzerSettings,
            },
          };
        });
      },

      mergeSavedSettings: (analyzer, profiles) => {
        set((state) => ({
          savedSettings: {
            ...state.savedSettings,
            [analyzer]: {
              ...state.savedSettings[analyzer],
              ...profiles,
            },
          },
        }));
      },
    }),
    {
      name: "polyanalyzer-settings",
      merge: (persisted, current) => {
        const saved = persisted as {
          language?: string;
          analyzerSettings?: unknown;
          savedSettings?: unknown;
        } | undefined;
        return {
          ...current,
          language: saved?.language ?? current.language,
          analyzerSettings: normalizeAnalyzerSettings(saved?.analyzerSettings),
          savedSettings: normalizeSavedSettings(saved?.savedSettings),
        };
      },
    },
  ),
);
