import { useCallback, useEffect } from "react";
import {
  type AnalyzerSettings,
  type SettingsAnalyzer,
  useSettingsStore,
} from "../stores/settingsStore";
import type { SendRpcRequest } from "../types/rpc";
import {
  fromBackendSettings,
  fromProfileFile,
  toBackendSettings,
  toProfileFile,
} from "../core/analysisProfiles";

export function useAnalysisProfiles(
  analyzer: SettingsAnalyzer,
  sendRequest: SendRpcRequest,
) {
  useEffect(() => {
    let cancelled = false;

    const synchronize = async () => {
      const response = await sendRequest("settings.list", { type: analyzer });
      const state = useSettingsStore.getState();
      const localProfiles = state.savedSettings[analyzer];
      const remoteProfiles: Record<string, AnalyzerSettings> = {};

      for (const filename of response.settings) {
        const loaded = await sendRequest("settings.load", {
          type: analyzer,
          name: filename,
        });
        const displayName = fromProfileFile(analyzer, filename);
        const base = localProfiles[displayName] ?? state.analyzerSettings[analyzer];
        remoteProfiles[displayName] = fromBackendSettings(base, loaded.setting);
      }

      const remoteNames = new Set(response.settings.map((name) => fromProfileFile(analyzer, name)));
      for (const [name, settings] of Object.entries(localProfiles)) {
        if (remoteNames.has(name)) continue;
        await sendRequest("settings.save", {
          type: analyzer,
          name: toProfileFile(analyzer, name),
          setting: toBackendSettings(settings),
        });
      }

      if (!cancelled) {
        useSettingsStore.getState().mergeSavedSettings(analyzer, remoteProfiles);
      }
    };

    void synchronize().catch((error) => {
      console.warn(`[${analyzer}-profiles] synchronization failed`, error);
    });
    return () => {
      cancelled = true;
    };
  }, [analyzer, sendRequest]);

  const saveProfile = useCallback(async (name: string) => {
    const state = useSettingsStore.getState();
    state.saveSettings(analyzer, name);
    await sendRequest("settings.save", {
      type: analyzer,
      name: toProfileFile(analyzer, name),
      setting: toBackendSettings(state.analyzerSettings[analyzer]),
    });
  }, [analyzer, sendRequest]);

  const deleteProfile = useCallback(async (name: string) => {
    if (name === "default") return;
    useSettingsStore.getState().deleteSettings(analyzer, name);
    await sendRequest("settings.delete", {
      type: analyzer,
      name: toProfileFile(analyzer, name),
    });
  }, [analyzer, sendRequest]);

  return { saveProfile, deleteProfile };
}
