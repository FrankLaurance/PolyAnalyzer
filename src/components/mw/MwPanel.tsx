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
  Tag,
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
import { openPath } from "@tauri-apps/plugin-opener";
import { usePythonBridge } from "../../hooks/usePythonBridge";
import { useAnalysisStore } from "../../stores/analysisStore";
import { useSettingsStore } from "../../stores/settingsStore";
import ProgressBar from "../common/ProgressBar";
import SettingsPanel from "../common/SettingsPanel";

export default function MwPanel() {
  const { t } = useTranslation();
  const { sendRequest, lastProgress } = usePythonBridge();
  const analyzer = useAnalysisStore((s) => s.analyzers.mw);
  const { setRunning, setResult, setProgress, reset } = useAnalysisStore();
  const {
    analyzerSettings,
    updateAnalyzerSettings,
    savedSettings,
    loadSettings,
    saveSettings,
    deleteSettings,
  } = useSettingsStore();

  const [folderPath, setFolderPath] = useState("");
  const [fileList, setFileList] = useState<string[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [saveImage, setSaveImage] = useState(true);
  const [displayImage, setDisplayImage] = useState(true);
  const [splitPositions, setSplitPositions] = useState<number[]>([]);
  const [newPosition, setNewPosition] = useState<number | null>(null);
  const [currentSetting, setCurrentSetting] = useState<string>();

  useEffect(() => {
    if (analyzer.running) {
      setProgress("mw", lastProgress.progress * 100, lastProgress.message);
    }
  }, [analyzer.running, lastProgress, setProgress]);

  const handleBrowse = async () => {
    const selected = await open({ directory: true, multiple: false });
    if (selected) {
      setFolderPath(selected as string);
      await loadFiles(selected as string);
    }
  };

  const loadFiles = async (path: string) => {
    try {
      const res = (await sendRequest("mw.list_files", {
        datadir: path,
      })) as { files: string[] };
      const result = res?.files;
      setFileList(result ?? []);
      setSelectedFiles(result ?? []);
    } catch {
      setFileList([]);
    }
  };

  const handleAddPosition = () => {
    if (newPosition !== null && !splitPositions.includes(newPosition)) {
      setSplitPositions([...splitPositions, newPosition].sort((a, b) => a - b));
      setNewPosition(null);
    }
  };

  const handleRemovePosition = (pos: number) => {
    setSplitPositions(splitPositions.filter((p) => p !== pos));
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
    reset("mw");
    setRunning("mw", true);
    try {
      const result = await sendRequest("mw.analyze", {
        datadir: folderPath,
        selected_files: selectedFiles,
        save_picture: saveImage,
        display_picture: displayImage,
        segmentpos: splitPositions,
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
      setResult("mw", {
        success: true,
        message: "Mw analysis complete",
        data: result,
      });
      message.success(t("complete", { time: "—" }));
    } catch (err) {
      setResult("mw", {
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
            onBlur={() => folderPath && loadFiles(folderPath)}
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
            checked={saveImage}
            onChange={(e) => setSaveImage(e.target.checked)}
          >
            {t("save_image")}
          </Checkbox>
          <Checkbox
            checked={displayImage}
            onChange={(e) => setDisplayImage(e.target.checked)}
          >
            {t("display_image")}
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
                      updateAnalyzerSettings({ drawBar: e.target.checked })
                    }
                  >
                    {t("draw_bar")}
                  </Checkbox>
                  <Checkbox
                    checked={analyzerSettings.drawMw}
                    onChange={(e) =>
                      updateAnalyzerSettings({ drawMw: e.target.checked })
                    }
                  >
                    {t("draw_mw")}
                  </Checkbox>
                  <Checkbox
                    checked={analyzerSettings.drawTable}
                    onChange={(e) =>
                      updateAnalyzerSettings({ drawTable: e.target.checked })
                    }
                  >
                    {t("draw_table")}
                  </Checkbox>
                  <Checkbox
                    checked={analyzerSettings.transparentBackground}
                    onChange={(e) =>
                      updateAnalyzerSettings({
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
                      updateAnalyzerSettings({ barColor: c.toHexString() })
                    }
                  />
                </div>
                <div className="color-row">
                  <label>{t("mw_color")}:</label>
                  <ColorPicker
                    value={analyzerSettings.mwColor}
                    onChange={(c) =>
                      updateAnalyzerSettings({ mwColor: c.toHexString() })
                    }
                  />
                </div>
                <div className="color-row">
                  <label>{t("curve_color")}:</label>
                  <ColorPicker
                    value={analyzerSettings.curveColor}
                    onChange={(c) =>
                      updateAnalyzerSettings({ curveColor: c.toHexString() })
                    }
                  />
                </div>

                <div className="slider-row">
                  <label>{t("bar_width")}:</label>
                  <Slider
                    min={0.1}
                    max={3}
                    step={0.1}
                    value={analyzerSettings.barWidth}
                    onChange={(v) => updateAnalyzerSettings({ barWidth: v })}
                  />
                </div>
                <div className="slider-row">
                  <label>{t("line_width")}:</label>
                  <Slider
                    min={0.5}
                    max={5}
                    step={0.1}
                    value={analyzerSettings.lineWidth}
                    onChange={(v) => updateAnalyzerSettings({ lineWidth: v })}
                  />
                </div>
                <div className="slider-row">
                  <label>{t("axis_width")}:</label>
                  <Slider
                    min={0.5}
                    max={5}
                    step={0.1}
                    value={analyzerSettings.axisWidth}
                    onChange={(v) => updateAnalyzerSettings({ axisWidth: v })}
                  />
                </div>
                <div className="slider-row">
                  <label>{t("title_font_size")}:</label>
                  <Slider
                    min={8}
                    max={32}
                    step={1}
                    value={analyzerSettings.titleFontSize}
                    onChange={(v) =>
                      updateAnalyzerSettings({ titleFontSize: v })
                    }
                  />
                </div>
                <div className="slider-row">
                  <label>{t("axis_font_size")}:</label>
                  <Slider
                    min={8}
                    max={32}
                    step={1}
                    value={analyzerSettings.axisFontSize}
                    onChange={(v) =>
                      updateAnalyzerSettings({ axisFontSize: v })
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
                  <div style={{ marginTop: 4 }}>
                    {splitPositions.map((pos) => (
                      <Tag
                        key={pos}
                        closable
                        onClose={() => handleRemovePosition(pos)}
                      >
                        {pos}
                      </Tag>
                    ))}
                    {splitPositions.length === 0 && (
                      <span style={{ color: "var(--color-text-secondary)" }}>
                        —
                      </span>
                    )}
                  </div>
                </div>
                <Space.Compact>
                  <InputNumber
                    value={newPosition}
                    onChange={(v) => setNewPosition(v)}
                    placeholder={t("new_split_position")}
                    step={0.1}
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
          options={fileList.map((f) => ({ label: f, value: f }))}
          placeholder={t("file_list")}
        />
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
