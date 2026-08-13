import { describe, expect, it } from "vitest";
import {
  fromBackendSettings,
  fromProfileFile,
  toBackendSettings,
  toProfileFile,
} from "../core/analysisProfiles";
import type { AnalyzerSettings } from "../stores/settingsStore";

describe("analysis profile mapping", () => {
  it("maps default profile names for every analyzer", () => {
    expect(toProfileFile("mw", "default")).toBe("defaultSetting.ini");
    expect(toProfileFile("dsc", "default")).toBe("defaultDSCSetting.ini");
    expect(toProfileFile("ir", "default")).toBe("defaultIRSetting.ini");
    expect(fromProfileFile("ir", "custom.ini")).toBe("custom");
  });

  it("round-trips shared profile values", () => {
    const original: AnalyzerSettings = {
      segmentpos: [0, 5000, 10000],
      barColor: "#002FA7",
      mwColor: "#FF6A07",
      curveColor: "#D62728",
      transparentBackground: true,
      drawBar: true,
      drawMw: true,
      drawTable: true,
      barWidth: 1.2,
      lineWidth: 1,
      axisWidth: 1,
      titleFontSize: 20,
      axisFontSize: 14,
      drawOverlay: false,
      normalizeOverlay: true,
      normalizationPeak: 1377,
    };

    const restored = fromBackendSettings(original, toBackendSettings("mw", original));

    expect(restored).toEqual(original);
  });

  it("round-trips segmentpos for the mw analyzer", () => {
    const original: AnalyzerSettings = {
      segmentpos: [0, 1000, 50000, 1000000],
      barColor: "#002FA7",
      mwColor: "#FF6A07",
      curveColor: "#002FA7",
      transparentBackground: true,
      drawBar: true,
      drawMw: true,
      drawTable: true,
      barWidth: 1.2,
      lineWidth: 1,
      axisWidth: 1,
      titleFontSize: 20,
      axisFontSize: 14,
      drawOverlay: true,
      normalizeOverlay: true,
      normalizationPeak: 1450,
    };

    const backend = toBackendSettings("mw", original);
    expect(backend.segmentpos).toEqual([0, 1000, 50000, 1000000]);

    const restored = fromBackendSettings(original, backend);
    expect(restored.segmentpos).toEqual([0, 1000, 50000, 1000000]);
  });

  it("keeps segmentpos out of dsc and ir profiles", () => {
    const original: AnalyzerSettings = {
      segmentpos: [0, 5000],
      barColor: "#002FA7",
      mwColor: "#FF6A07",
      curveColor: "#D62728",
      transparentBackground: true,
      drawBar: true,
      drawMw: true,
      drawTable: true,
      barWidth: 1.2,
      lineWidth: 1,
      axisWidth: 1,
      titleFontSize: 20,
      axisFontSize: 14,
      drawOverlay: true,
      normalizeOverlay: true,
      normalizationPeak: 1450,
    };

    expect(toBackendSettings("dsc", original)).not.toHaveProperty("segmentpos");
    expect(toBackendSettings("ir", original)).not.toHaveProperty("segmentpos");
  });

  it("falls back to the base segmentpos when the backend value is invalid", () => {
    const base: AnalyzerSettings = {
      segmentpos: [0, 5000],
      barColor: "#002FA7",
      mwColor: "#FF6A07",
      curveColor: "#002FA7",
      transparentBackground: true,
      drawBar: true,
      drawMw: true,
      drawTable: true,
      barWidth: 1.2,
      lineWidth: 1,
      axisWidth: 1,
      titleFontSize: 20,
      axisFontSize: 14,
      drawOverlay: true,
      normalizeOverlay: true,
      normalizationPeak: 1450,
    };

    expect(fromBackendSettings(base, { segmentpos: "bad" }).segmentpos).toEqual([0, 5000]);
    expect(fromBackendSettings(base, { segmentpos: [1, "x", 3] }).segmentpos).toEqual([1, 3]);
    expect(fromBackendSettings(base, {}).segmentpos).toEqual([0, 5000]);
  });
});
