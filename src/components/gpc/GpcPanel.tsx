import { useState } from "react";
import {
  Button,
  Input,
  Checkbox,
  Select,
  Collapse,
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

export default function GpcPanel() {
  const { t } = useTranslation();
  const { sendRequest } = usePythonBridge();
  const analyzer = useAnalysisStore((s) => s.analyzers.gpc);
  const { setRunning, setResult, reset } = useAnalysisStore();
  const { savedSettings, loadSettings, saveSettings, deleteSettings } =
    useSettingsStore();

  const [folderPath, setFolderPath] = useState("");
  const [outputFilename, setOutputFilename] = useState("");
  const [fileList, setFileList] = useState<string[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [saveSampleInfo, setSaveSampleInfo] = useState(true);
  const [saveImage, setSaveImage] = useState(true);
  const [displayImage, setDisplayImage] = useState(true);
  const [savePlotData, setSavePlotData] = useState(false);
  const [selectPartial, setSelectPartial] = useState(false);
  const [confirmOverwrite, setConfirmOverwrite] = useState(false);
  const [currentSetting, setCurrentSetting] = useState<string>();

  const handleBrowse = async () => {
    const selected = await open({ directory: true, multiple: false });
    if (selected) {
      setFolderPath(selected as string);
      await loadFiles(selected as string);
    }
  };

  const loadFiles = async (path: string) => {
    try {
      const result = (await sendRequest("list_files", {
        path,
        type: "gpc",
      })) as string[];
      setFileList(result ?? []);
      setSelectedFiles(result ?? []);
    } catch {
      setFileList([]);
    }
  };

  const handleRun = async () => {
    if (!folderPath) {
      message.warning(t("invalid_path"));
      return;
    }
    reset("gpc");
    setRunning("gpc", true);
    try {
      const result = await sendRequest("run_gpc", {
        folder: folderPath,
        output_filename: outputFilename,
        files: selectPartial ? selectedFiles : undefined,
        save_sample_info: saveSampleInfo,
        save_image: saveImage,
        display_image: displayImage,
        save_plot_data: savePlotData,
        confirm_overwrite: confirmOverwrite,
      });
      setResult("gpc", {
        success: true,
        message: "GPC analysis complete",
        data: result,
      });
      message.success(t("complete", { time: "—" }));
    } catch (err) {
      setResult("gpc", {
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

        <div className="panel-row">
          <label>{t("output_filename")}:</label>
          <Input
            style={{ width: 300 }}
            value={outputFilename}
            onChange={(e) => setOutputFilename(e.target.value)}
            placeholder={t("output_filename")}
          />
        </div>
      </div>

      {/* Options */}
      <div className="panel-section">
        <div className="checkbox-group">
          <Checkbox
            checked={saveSampleInfo}
            onChange={(e) => setSaveSampleInfo(e.target.checked)}
          >
            {t("save_sample_info")}
          </Checkbox>
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
          <Checkbox
            checked={savePlotData}
            onChange={(e) => setSavePlotData(e.target.checked)}
          >
            {t("save_plot_data")}
          </Checkbox>
          <Checkbox
            checked={selectPartial}
            onChange={(e) => setSelectPartial(e.target.checked)}
          >
            {t("select_partial_files")}
          </Checkbox>
        </div>
      </div>

      {/* File list */}
      {selectPartial && (
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
      )}

      {/* Overwrite confirmation */}
      <div className="panel-section">
        <Checkbox
          checked={confirmOverwrite}
          onChange={(e) => setConfirmOverwrite(e.target.checked)}
        >
          {t("confirm_overwrite")} — {t("file_exists_warning")}
        </Checkbox>
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
