import { create } from "zustand";

export type AnalyzerType = "gpc" | "mw" | "dsc" | "other";

interface AnalysisResult {
  success: boolean;
  message: string;
  data?: unknown;
  elapsedTime?: number;
}

interface AnalyzerState {
  progress: number;
  message: string;
  running: boolean;
  result: AnalysisResult | null;
}

interface AnalysisState {
  analyzers: Record<AnalyzerType, AnalyzerState>;
  setProgress: (type: AnalyzerType, progress: number, message: string) => void;
  setRunning: (type: AnalyzerType, running: boolean) => void;
  setResult: (type: AnalyzerType, result: AnalysisResult | null) => void;
  reset: (type: AnalyzerType) => void;
}

const defaultAnalyzerState: AnalyzerState = {
  progress: 0,
  message: "",
  running: false,
  result: null,
};

export const useAnalysisStore = create<AnalysisState>()((set) => ({
  analyzers: {
    gpc: { ...defaultAnalyzerState },
    mw: { ...defaultAnalyzerState },
    dsc: { ...defaultAnalyzerState },
    other: { ...defaultAnalyzerState },
  },

  setProgress: (type, progress, message) => {
    set((s) => ({
      analyzers: {
        ...s.analyzers,
        [type]: { ...s.analyzers[type], progress, message },
      },
    }));
  },

  setRunning: (type, running) => {
    set((s) => ({
      analyzers: {
        ...s.analyzers,
        [type]: { ...s.analyzers[type], running },
      },
    }));
  },

  setResult: (type, result) => {
    set((s) => ({
      analyzers: {
        ...s.analyzers,
        [type]: { ...s.analyzers[type], result, running: false },
      },
    }));
  },

  reset: (type) => {
    set((s) => ({
      analyzers: {
        ...s.analyzers,
        [type]: { ...defaultAnalyzerState },
      },
    }));
  },
}));
