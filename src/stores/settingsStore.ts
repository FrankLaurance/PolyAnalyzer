import { create } from "zustand";
import { persist } from "zustand/middleware";
import i18n from "../i18n";

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
};

interface SettingsState {
  language: string;
  analyzerSettings: AnalyzerSettings;
  savedSettings: Record<string, AnalyzerSettings>;
  setLanguage: (lang: string) => void;
  updateAnalyzerSettings: (patch: Partial<AnalyzerSettings>) => void;
  saveSettings: (name: string) => void;
  loadSettings: (name: string) => void;
  deleteSettings: (name: string) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      language: localStorage.getItem("polyanalyzer-language") || "zh_CN",
      analyzerSettings: { ...defaultAnalyzerSettings },
      savedSettings: {},

      setLanguage: (lang: string) => {
        i18n.changeLanguage(lang);
        localStorage.setItem("polyanalyzer-language", lang);
        set({ language: lang });
      },

      updateAnalyzerSettings: (patch: Partial<AnalyzerSettings>) => {
        set((s) => ({
          analyzerSettings: { ...s.analyzerSettings, ...patch },
        }));
      },

      saveSettings: (name: string) => {
        set((s) => ({
          savedSettings: {
            ...s.savedSettings,
            [name]: { ...s.analyzerSettings },
          },
        }));
      },

      loadSettings: (name: string) => {
        const saved = get().savedSettings[name];
        if (saved) {
          set({ analyzerSettings: { ...saved } });
        }
      },

      deleteSettings: (name: string) => {
        set((s) => {
          const next = { ...s.savedSettings };
          delete next[name];
          return { savedSettings: next };
        });
      },
    }),
    {
      name: "polyanalyzer-settings",
    },
  ),
);
