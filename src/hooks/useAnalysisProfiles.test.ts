import { describe, expect, it } from "vitest";
import {
  fromBackendSettings,
  fromProfileFile,
  toBackendSettings,
  toProfileFile,
} from "../core/analysisProfiles";

describe("analysis profile mapping", () => {
  it("maps default profile names for every analyzer", () => {
    expect(toProfileFile("mw", "default")).toBe("defaultSetting.ini");
    expect(toProfileFile("dsc", "default")).toBe("defaultDSCSetting.ini");
    expect(toProfileFile("ir", "default")).toBe("defaultIRSetting.ini");
    expect(fromProfileFile("ir", "custom.ini")).toBe("custom");
  });

  it("round-trips shared profile values", () => {
    const original = {
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

    const restored = fromBackendSettings(original, toBackendSettings(original));

    expect(restored).toEqual(original);
  });
});
