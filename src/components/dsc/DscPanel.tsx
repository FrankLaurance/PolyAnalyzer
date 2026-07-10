import { useState, useEffect } from "react";
import {
  Button,
  Input,
  Checkbox,
  Collapse,
  Slider,
  ColorPicker,
  Space,
  Select,
  Alert,
  message,
} from "antd";
import {
  FolderOpenOutlined,
  PlayCircleOutlined,
  FolderViewOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { open } from "@tauri-apps/plugin-dialog";
import { invoke } from "@tauri-apps/api/core";
import { usePythonBridge } from "../../hooks/usePythonBridge";
import { getErrorMessage, useAnalyzerFiles } from "../../hooks/useAnalyzerFiles";
import { useAnalysisStore } from "../../stores/analysisStore";
import { useSettingsStore } from "../../stores/settingsStore";
import ProgressBar from "../common/ProgressBar";
import SettingsPanel from "../common/SettingsPanel";

export default function DscPanel() {
  const { t } = useTranslation();
  const { sendRequest, lastProgress } = usePythonBridge("dsc");
  const analyzer = useAnalysisStore((s) => s.analyzers.dsc);
  const { setRunning, setResult, setProgress, reset } = useAnalysisStore();
  const analyzerSettings = useSettingsStore((s) => s.analyzerSettings.dsc);
  const savedSettings = useSettingsStore((s) => s.savedSettings.dsc);
  const updateAnalyzerSettings = useSettingsStore((s) => s.updateAnalyzerSettings);
  const loadSettings = useSettingsStore((s) => s.loadSettings);
  const saveSettings = useSettingsStore((s) => s.saveSettings);
  const deleteSettings = useSettingsStore((s) => s.deleteSettings);

  const [folderPath, setFolderPath] = useState("");
  const {
    fileList,
    selectedFiles,
    setSelectedFiles,
    filesLoading,
    fileError,
    clearFiles,
    loadFiles,
  } = useAnalyzerFiles(sendRequest, "dsc.list_files");
  const [saveSegmentData, setSaveSegmentData] = useState(true);
  const [drawSegmentCurve, setDrawSegmentCurve] = useState(true);
  const [drawCycleComparison, setDrawCycleComparison] = useState(true);
  const [saveComparison, setSaveComparison] = useState(true);
  const [peaksUpward, setPeaksUpward] = useState(false);
  const [centerPeak, setCenterPeak] = useState(false);
  const [leftBoundary, setLeftBoundary] = useState(1.9);
  const [rightBoundary, setRightBoundary] = useState(1.9);
  const [currentSetting, setCurrentSetting] = useState<string>("default");
  const [outputDir, setOutputDir] = useState("");

  useEffect(() => {
    if (analyzer.running) {
      setProgress("dsc", lastProgress.progress * 100, lastProgress.message);
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
    reset("dsc");
    setRunning("dsc", true);
    try {
      const drawCycle = saveSegmentData && drawCycleComparison;
      const result = await sendRequest("dsc.analyze", {
        datadir: folderPath,
        selected_files: selectedFiles,
        save_seg_mode: saveSegmentData,
        draw_seg_mode: drawSegmentCurve,
        draw_cycle: drawCycle,
        display_pic: false,
        save_cycle_pic: drawCycle && saveComparison,
        peaks_upward: peaksUpward,
        center_peak: centerPeak,
        left_length: leftBoundary,
        right_length: rightBoundary,
        curve_color: analyzerSettings.curveColor,
        line_width: analyzerSettings.lineWidth,
        axis_width: analyzerSettings.axisWidth,
        title_font_size: analyzerSettings.titleFontSize,
        axis_font_size: analyzerSettings.axisFontSize,
        transparent_back: analyzerSettings.transparentBackground,
      });
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      const res = result as { cycle_dir?: string; pic_dir?: string };
      if (res?.pic_dir) setOutputDir(res.pic_dir);
      else if (res?.cycle_dir) setOutputDir(res.cycle_dir);
      setProgress("dsc", 100, t("complete", { time: elapsed }));
      setResult("dsc", {
        success: true,
        message: "DSC analysis complete",
        data: result,
      });
      message.success(t("complete", { time: elapsed }));
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setResult("dsc", {
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
          options={fileList.map((file) => ({ label: file, value: file }))}
          placeholder={t("file_list")}
        />
        {fileError && <Alert type="error" showIcon message={fileError} />}
      </div>

      {/* Options — with dependency logic matching original */}
      <div className="panel-section">
        <div className="checkbox-group">
          <Checkbox
            checked={saveSegmentData}
            onChange={(e) => setSaveSegmentData(e.target.checked)}
          >
            {t("save_segment_data")}
          </Checkbox>
          <Checkbox
            checked={drawSegmentCurve}
            onChange={(e) => setDrawSegmentCurve(e.target.checked)}
          >
            {t("draw_segment_data")}
          </Checkbox>
          <Checkbox
            checked={drawCycleComparison}
            disabled={!saveSegmentData}
            onChange={(e) => setDrawCycleComparison(e.target.checked)}
          >
            {t("draw_cycle")}
          </Checkbox>
          <Checkbox
            checked={saveComparison}
            disabled={!saveSegmentData || !drawCycleComparison}
            onChange={(e) => setSaveComparison(e.target.checked)}
          >
            {t("save_cycle")}
          </Checkbox>
          <Checkbox
            checked={peaksUpward}
            onChange={(e) => setPeaksUpward(e.target.checked)}
          >
            {t("peaks_upward")}
          </Checkbox>
          <Checkbox
            checked={centerPeak}
            onChange={(e) => setCenterPeak(e.target.checked)}
          >
            {t("center_peak")}
          </Checkbox>
        </div>
      </div>

      {/* Boundary sliders */}
      <div className="panel-section">
        <div className="slider-row">
          <label>{t("left_boundary")}:</label>
          <Slider
            min={0}
            max={3}
            step={0.1}
            value={leftBoundary}
            onChange={setLeftBoundary}
          />
          <span style={{ minWidth: 36 }}>{leftBoundary}</span>
        </div>
        <div className="slider-row">
          <label>{t("right_boundary")}:</label>
          <Slider
            min={0}
            max={3}
            step={0.1}
            value={rightBoundary}
            onChange={setRightBoundary}
          />
          <span style={{ minWidth: 36 }}>{rightBoundary}</span>
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
                    checked={analyzerSettings.transparentBackground}
                    onChange={(e) =>
                      updateAnalyzerSettings("dsc", {
                        transparentBackground: e.target.checked,
                      })
                    }
                  >
                    {t("transparent_background")}
                  </Checkbox>
                </div>

                <div className="color-row">
                  <label>{t("curve_color")}:</label>
                  <ColorPicker
                    value={analyzerSettings.curveColor}
                    onChange={(c) =>
                      updateAnalyzerSettings("dsc", { curveColor: c.toHexString() })
                    }
                  />
                </div>

                <div className="slider-row">
                  <label>{t("line_width")}:</label>
                  <Slider
                    min={0.2}
                    max={3.0}
                    step={0.1}
                    value={analyzerSettings.lineWidth}
                    onChange={(v) => updateAnalyzerSettings("dsc", { lineWidth: v })}
                  />
                </div>
                <div className="slider-row">
                  <label>{t("axis_width")}:</label>
                  <Slider
                    min={0.5}
                    max={3.0}
                    step={0.1}
                    value={analyzerSettings.axisWidth}
                    onChange={(v) => updateAnalyzerSettings("dsc", { axisWidth: v })}
                  />
                </div>
                <div className="slider-row">
                  <label>{t("title_font_size")}:</label>
                  <Slider
                    min={10}
                    max={28}
                    step={1}
                    value={analyzerSettings.titleFontSize}
                    onChange={(v) =>
                      updateAnalyzerSettings("dsc", { titleFontSize: v })
                    }
                  />
                </div>
                <div className="slider-row">
                  <label>{t("axis_font_size")}:</label>
                  <Slider
                    min={8}
                    max={24}
                    step={1}
                    value={analyzerSettings.axisFontSize}
                    onChange={(v) =>
                      updateAnalyzerSettings("dsc", { axisFontSize: v })
                    }
                  />
                </div>
              </div>
            ),
          },
        ]}
      />

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

      {/* Settings */}
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
                  loadSettings("dsc", name);
                }}
                onSave={(name) => {
                  saveSettings("dsc", name);
                  setCurrentSetting(name);
                }}
                onDelete={(name) => {
                  deleteSettings("dsc", name);
                  setCurrentSetting("");
                }}
              />
            ),
          },
        ]}
      />
    </div>
  );
}
