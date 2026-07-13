import { useState, useEffect } from "react";
import {
  Button,
  Input,
  Checkbox,
  Select,
  Collapse,
  Slider,
  ColorPicker,
  Space,
  InputNumber,
  Alert,
  message,
} from "antd";
import {
  FolderOpenOutlined,
  PlayCircleOutlined,
  FolderViewOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { open } from "@tauri-apps/plugin-dialog";
import { invoke } from "@tauri-apps/api/core";
import { usePythonBridge } from "../../hooks/usePythonBridge";
import { getErrorMessage, useAnalyzerFiles } from "../../hooks/useAnalyzerFiles";
import { useAnalysisProfiles } from "../../hooks/useAnalysisProfiles";
import { useAnalysisStore } from "../../stores/analysisStore";
import { useSettingsStore } from "../../stores/settingsStore";
import ProgressBar from "../common/ProgressBar";
import SettingsPanel from "../common/SettingsPanel";

const DEFAULT_SEGMENT_POSITIONS = [
  0, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000, 10000000, 50000000,
];

export default function MwPanel() {
  const { t } = useTranslation();
  const { sendRequest, lastProgress } = usePythonBridge("mw");
  const analyzer = useAnalysisStore((s) => s.analyzers.mw);
  const { setRunning, setResult, setProgress, reset } = useAnalysisStore();
  const analyzerSettings = useSettingsStore((s) => s.analyzerSettings.mw);
  const savedSettings = useSettingsStore((s) => s.savedSettings.mw);
  const updateAnalyzerSettings = useSettingsStore((s) => s.updateAnalyzerSettings);
  const loadSettings = useSettingsStore((s) => s.loadSettings);
  const { saveProfile, deleteProfile } = useAnalysisProfiles("mw", sendRequest);

  const [folderPath, setFolderPath] = useState("");
  const {
    fileList,
    selectedFiles,
    setSelectedFiles,
    filesLoading,
    fileError,
    clearFiles,
    loadFiles,
  } = useAnalyzerFiles(sendRequest, "mw.list_files");
  const [saveImage, setSaveImage] = useState(true);
  const [allPositions, setAllPositions] = useState<number[]>([...DEFAULT_SEGMENT_POSITIONS]);
  const [selectedPositions, setSelectedPositions] = useState<number[]>([...DEFAULT_SEGMENT_POSITIONS]);
  const [newPosition, setNewPosition] = useState<number | null>(null);
  const [currentSetting, setCurrentSetting] = useState<string>("default");
  const [outputDir, setOutputDir] = useState("");

  useEffect(() => {
    if (analyzer.running) {
      setProgress("mw", lastProgress.progress * 100, lastProgress.message);
    }
  }, [analyzer.running, lastProgress, setProgress]);

  useEffect(() => {
    sendRequest("system.get_default_datapath", {})
      .then((res) => {
        const dp = (res as { datapath: string })?.datapath;
        if (dp) {
          setFolderPath(dp);
          void loadFiles(dp);
        }
      })
      .catch((error) => message.error(getErrorMessage(error)));
  }, [loadFiles, sendRequest]);

  const handleFolderPathChange = (path: string) => {
    setFolderPath(path);
    clearFiles();
  };

  const handleBrowse = async () => {
    const selected = await open({ directory: true, multiple: false });
    if (selected) {
      const path = selected as string;
      handleFolderPathChange(path);
      await loadFiles(path);
    }
  };

  const handleAddPosition = () => {
    if (newPosition !== null && !allPositions.includes(newPosition)) {
      const updated = [...allPositions, newPosition].sort((a, b) => a - b);
      setAllPositions(updated);
      setSelectedPositions([...selectedPositions, newPosition].sort((a, b) => a - b));
      setNewPosition(null);
    }
  };

  const handleRun = async () => {
    if (!folderPath) {
      message.warning(t("invalid_path"));
      return;
    }
    if (selectedFiles.length === 0) {
      message.warning(t("select_at_least_one"));
      return;
    }
    const startTime = Date.now();
    reset("mw");
    setRunning("mw", true);
    try {
      const result = await sendRequest("mw.analyze", {
        datadir: folderPath,
        selected_files: selectedFiles,
        save_picture: saveImage,
        display_picture: false,
        segmentpos: selectedPositions,
        bar_color: analyzerSettings.barColor,
        mw_color: analyzerSettings.mwColor,
        bar_width: analyzerSettings.barWidth,
        line_width: analyzerSettings.lineWidth,
        axis_width: analyzerSettings.axisWidth,
        title_font_size: analyzerSettings.titleFontSize,
        axis_font_size: analyzerSettings.axisFontSize,
        transparent_back: analyzerSettings.transparentBackground,
        draw_bar: analyzerSettings.drawBar,
        draw_mw: analyzerSettings.drawMw,
        draw_table: analyzerSettings.drawTable,
      });
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      const res = result as { output_dir?: string };
      if (res?.output_dir) setOutputDir(res.output_dir);
      setProgress("mw", 100, t("complete", { time: elapsed }));
      setResult("mw", {
        success: true,
        message: "Mw analysis complete",
        data: result,
      });
      message.success(t("complete", { time: elapsed }));
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setResult("mw", {
        success: false,
        message: errorMessage,
      });
      message.error(errorMessage);
    }
  };

  const handleOpenFolder = async () => {
    const target = outputDir || folderPath;
    if (!target) return;
    try {
      await invoke("open_folder", { path: target });
    } catch (error) {
      message.error(getErrorMessage(error));
    }
  };

  return (
    <div className="panel-container">
      {/* Folder input */}
      <div className="panel-section">
        <div className="panel-row">
          <label>{t("data_folder")}:</label>
          <Input
            className="folder-input"
            value={folderPath}
            onChange={(e) => handleFolderPathChange(e.target.value)}
            onBlur={() => folderPath && void loadFiles(folderPath)}
            placeholder={t("data_folder")}
            disabled={analyzer.running}
          />
          <Button
            icon={<FolderOpenOutlined />}
            onClick={handleBrowse}
            disabled={analyzer.running}
          >
            {t("open_folder")}
          </Button>
        </div>
      </div>

      {/* Options */}
      <div className="panel-section">
        <div className="checkbox-group">
          <Checkbox
            checked={saveImage}
            onChange={(e) => setSaveImage(e.target.checked)}
          >
            {t("save_image")}
          </Checkbox>
        </div>
      </div>

      {/* Plot settings */}
      <Collapse
        className="settings-collapse"
        items={[
          {
            key: "plot",
            label: t("plot_settings"),
            children: (
              <div>
                <div className="checkbox-group" style={{ marginBottom: 16 }}>
                  <Checkbox
                    checked={analyzerSettings.drawBar}
                    onChange={(e) =>
                      updateAnalyzerSettings("mw", { drawBar: e.target.checked })
                    }
                  >
                    {t("draw_bar")}
                  </Checkbox>
                  <Checkbox
                    checked={analyzerSettings.drawMw}
                    onChange={(e) =>
                      updateAnalyzerSettings("mw", { drawMw: e.target.checked })
                    }
                  >
                    {t("draw_mw")}
                  </Checkbox>
                  <Checkbox
                    checked={analyzerSettings.drawTable}
                    onChange={(e) =>
                      updateAnalyzerSettings("mw", { drawTable: e.target.checked })
                    }
                  >
                    {t("draw_table")}
                  </Checkbox>
                  <Checkbox
                    checked={analyzerSettings.transparentBackground}
                    onChange={(e) =>
                      updateAnalyzerSettings("mw", {
                        transparentBackground: e.target.checked,
                      })
                    }
                  >
                    {t("transparent_background")}
                  </Checkbox>
                </div>

                <div className="color-row">
                  <label>{t("bar_color")}:</label>
                  <ColorPicker
                    value={analyzerSettings.barColor}
                    onChange={(c) =>
                      updateAnalyzerSettings("mw", { barColor: c.toHexString() })
                    }
                  />
                </div>
                <div className="color-row">
                  <label>{t("mw_color")}:</label>
                  <ColorPicker
                    value={analyzerSettings.mwColor}
                    onChange={(c) =>
                      updateAnalyzerSettings("mw", { mwColor: c.toHexString() })
                    }
                  />
                </div>

                <div className="slider-row">
                  <label>{t("bar_width")}:</label>
                  <Slider
                    min={0.2}
                    max={2.0}
                    step={0.1}
                    value={analyzerSettings.barWidth}
                    onChange={(v) => updateAnalyzerSettings("mw", { barWidth: v })}
                  />
                </div>
                <div className="slider-row">
                  <label>{t("line_width")}:</label>
                  <Slider
                    min={0.2}
                    max={2.0}
                    step={0.1}
                    value={analyzerSettings.lineWidth}
                    onChange={(v) => updateAnalyzerSettings("mw", { lineWidth: v })}
                  />
                </div>
                <div className="slider-row">
                  <label>{t("axis_width")}:</label>
                  <Slider
                    min={0.5}
                    max={2.0}
                    step={0.1}
                    value={analyzerSettings.axisWidth}
                    onChange={(v) => updateAnalyzerSettings("mw", { axisWidth: v })}
                  />
                </div>
                <div className="slider-row">
                  <label>{t("title_font_size")}:</label>
                  <Slider
                    min={14}
                    max={28}
                    step={1}
                    value={analyzerSettings.titleFontSize}
                    onChange={(v) =>
                      updateAnalyzerSettings("mw", { titleFontSize: v })
                    }
                  />
                </div>
                <div className="slider-row">
                  <label>{t("axis_font_size")}:</label>
                  <Slider
                    min={10}
                    max={18}
                    step={1}
                    value={analyzerSettings.axisFontSize}
                    onChange={(v) =>
                      updateAnalyzerSettings("mw", { axisFontSize: v })
                    }
                  />
                </div>
              </div>
            ),
          },
        ]}
      />

      {/* Region settings */}
      <Collapse
        className="settings-collapse"
        items={[
          {
            key: "region",
            label: t("region_settings"),
            children: (
              <div>
                <div style={{ marginBottom: 8 }}>
                  <label>{t("split_position")}:</label>
                  <Select
                    mode="multiple"
                    style={{ width: "100%", marginTop: 4 }}
                    value={selectedPositions}
                    onChange={(vals) =>
                      setSelectedPositions([...vals].sort((a, b) => a - b))
                    }
                    options={allPositions.map((p) => ({
                      label: p.toLocaleString(),
                      value: p,
                    }))}
                  />
                </div>
                <Space.Compact>
                  <InputNumber
                    value={newPosition}
                    onChange={(v) => setNewPosition(v)}
                    placeholder={t("new_split_position")}
                    min={0}
                    max={1000000000}
                    step={1}
                  />
                  <Button icon={<PlusOutlined />} onClick={handleAddPosition}>
                    {t("add_region")}
                  </Button>
                </Space.Compact>
              </div>
            ),
          },
        ]}
      />

      {/* File list */}
      <div className="panel-section">
        <label className="panel-section-title">{t("file_list")}</label>
        <Select
          mode="multiple"
          className="file-list-select"
          value={selectedFiles}
          onChange={setSelectedFiles}
          disabled={analyzer.running}
          loading={filesLoading}
          options={fileList.map((f) => ({ label: f, value: f }))}
          placeholder={t("file_list")}
        />
        {fileError && <Alert type="error" showIcon message={fileError} />}
      </div>

      {/* Actions */}
      <div className="panel-section">
        <Space className="panel-actions">
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleRun}
            loading={analyzer.running}
          >
            {t("run")}
          </Button>
          <Button icon={<FolderViewOutlined />} onClick={handleOpenFolder}>
            {t("open_folder")}
          </Button>
        </Space>
        <ProgressBar
          progress={analyzer.progress}
          message={analyzer.message}
          running={analyzer.running}
          failed={analyzer.result?.success === false}
        />
      </div>

      {/* Settings management */}
      <Collapse
        className="settings-collapse"
        items={[
          {
            key: "settings",
            label: t("settings"),
            children: (
              <SettingsPanel
                settingsList={Object.keys(savedSettings)}
                currentSetting={currentSetting}
                onSwitch={(name) => {
                  setCurrentSetting(name);
                  loadSettings("mw", name);
                }}
                onSave={(name) => {
                  setCurrentSetting(name);
                  void saveProfile(name).catch((error) => message.error(getErrorMessage(error)));
                }}
                onDelete={(name) => {
                  setCurrentSetting("default");
                  void deleteProfile(name).catch((error) => message.error(getErrorMessage(error)));
                }}
              />
            ),
          },
        ]}
      />
    </div>
  );
}
