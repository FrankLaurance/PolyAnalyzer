import { useState, useEffect } from "react";
import {
  Button,
  Input,
  Checkbox,
  Collapse,
  Slider,
  Space,
  message,
} from "antd";
import {
  FolderOpenOutlined,
  PlayCircleOutlined,
  FolderViewOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { open } from "@tauri-apps/plugin-dialog";
import { openPath } from "@tauri-apps/plugin-opener";
import { usePythonBridge } from "../../hooks/usePythonBridge";
import { useAnalysisStore } from "../../stores/analysisStore";
import { useSettingsStore } from "../../stores/settingsStore";
import ProgressBar from "../common/ProgressBar";
import SettingsPanel from "../common/SettingsPanel";

export default function DscPanel() {
  const { t } = useTranslation();
  const { sendRequest, lastProgress } = usePythonBridge();
  const analyzer = useAnalysisStore((s) => s.analyzers.dsc);
  const { setRunning, setResult, setProgress, reset } = useAnalysisStore();
  const { savedSettings, loadSettings, saveSettings, deleteSettings } =
    useSettingsStore();

  const [folderPath, setFolderPath] = useState("");
  const [saveSegmentData, setSaveSegmentData] = useState(true);
  const [drawSegmentCurve, setDrawSegmentCurve] = useState(true);
  const [drawCycleComparison, setDrawCycleComparison] = useState(true);
  const [displayComparison, setDisplayComparison] = useState(true);
  const [saveComparison, setSaveComparison] = useState(true);
  const [peaksUpward, setPeaksUpward] = useState(false);
  const [centerPeak, setCenterPeak] = useState(false);
  const [leftBoundary, setLeftBoundary] = useState(0);
  const [rightBoundary, setRightBoundary] = useState(3);
  const [currentSetting, setCurrentSetting] = useState<string>();

  useEffect(() => {
    if (analyzer.running) {
      setProgress("dsc", lastProgress.progress * 100, lastProgress.message);
    }
  }, [analyzer.running, lastProgress, setProgress]);

  const handleBrowse = async () => {
    const selected = await open({ directory: true, multiple: false });
    if (selected) {
      setFolderPath(selected as string);
    }
  };

  const handleRun = async () => {
    if (!folderPath) {
      message.warning(t("invalid_path"));
      return;
    }
    reset("dsc");
    setRunning("dsc", true);
    try {
      const result = await sendRequest("dsc.analyze", {
        datadir: folderPath,
        save_seg_mode: saveSegmentData,
        draw_seg_mode: drawSegmentCurve,
        draw_cycle: drawCycleComparison,
        display_pic: displayComparison,
        save_cycle_pic: saveComparison,
        peaks_upward: peaksUpward,
        center_peak: centerPeak,
        left_length: leftBoundary,
        right_length: rightBoundary,
      });
      setResult("dsc", {
        success: true,
        message: "DSC analysis complete",
        data: result,
      });
      message.success(t("complete", { time: "—" }));
    } catch (err) {
      setResult("dsc", {
        success: false,
        message: err instanceof Error ? err.message : String(err),
      });
      message.error(String(err));
    }
  };

  const handleOpenFolder = async () => {
    if (folderPath) {
      await openPath(folderPath);
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
            onChange={(e) => setFolderPath(e.target.value)}
            placeholder={t("data_folder")}
          />
          <Button icon={<FolderOpenOutlined />} onClick={handleBrowse}>
            {t("open_folder")}
          </Button>
        </div>
      </div>

      {/* Options */}
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
            onChange={(e) => setDrawCycleComparison(e.target.checked)}
          >
            {t("draw_cycle")}
          </Checkbox>
          <Checkbox
            checked={displayComparison}
            onChange={(e) => setDisplayComparison(e.target.checked)}
          >
            {t("display_cycle")}
          </Checkbox>
          <Checkbox
            checked={saveComparison}
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
                  loadSettings(name);
                }}
                onSave={(name) => {
                  saveSettings(name);
                  setCurrentSetting(name);
                }}
                onDelete={(name) => {
                  deleteSettings(name);
                  setCurrentSetting(undefined);
                }}
              />
            ),
          },
        ]}
      />
    </div>
  );
}
