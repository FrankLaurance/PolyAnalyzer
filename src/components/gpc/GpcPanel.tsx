import { useState, useEffect } from "react";
import {
  Button,
  Input,
  Checkbox,
  Select,
  Alert,
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
import { invoke } from "@tauri-apps/api/core";
import { usePythonBridge } from "../../hooks/usePythonBridge";
import { getErrorMessage, useAnalyzerFiles } from "../../hooks/useAnalyzerFiles";
import { useAnalysisStore } from "../../stores/analysisStore";
import ProgressBar from "../common/ProgressBar";

export default function GpcPanel() {
  const { t } = useTranslation();
  const { sendRequest, lastProgress } = usePythonBridge("gpc");
  const analyzer = useAnalysisStore((s) => s.analyzers.gpc);
  const { setRunning, setResult, setProgress, reset } = useAnalysisStore();

  const [folderPath, setFolderPath] = useState("");
  const [outputFilename, setOutputFilename] = useState(
    () => new Date().toISOString().slice(0, 10).replace(/-/g, "")
  );
  const {
    fileList,
    selectedFiles,
    setSelectedFiles,
    filesLoading,
    fileError,
    clearFiles,
    loadFiles,
  } = useAnalyzerFiles(sendRequest, "gpc.list_files");
  const [saveSampleInfo, setSaveSampleInfo] = useState(true);
  const [saveImage, setSaveImage] = useState(true);
  const [savePlotData, setSavePlotData] = useState(false);
  const [selectPartial, setSelectPartial] = useState(false);
  const [confirmOverwrite, setConfirmOverwrite] = useState(false);
  const [outputDir, setOutputDir] = useState("");

  useEffect(() => {
    if (analyzer.running) {
      setProgress("gpc", lastProgress.progress * 100, lastProgress.message);
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
    if (selectPartial && selectedFiles.length === 0) {
      message.warning(t("select_at_least_one"));
      return;
    }
    const fname = outputFilename.trim() || new Date().toISOString().slice(0, 10).replace(/-/g, "");
    const startTime = Date.now();
    reset("gpc");
    setRunning("gpc", true);
    try {
      const result = await sendRequest("gpc.analyze", {
        datadir: folderPath,
        output_filename: fname,
        selected_files: selectPartial ? selectedFiles : undefined,
        save_file: saveSampleInfo,
        save_picture: saveImage,
        display_mode: false,
        save_figure_file_gpc: savePlotData,
        confirm_overwrite: confirmOverwrite,
      });
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      const res = result as { output_dir?: string };
      if (res?.output_dir) setOutputDir(res.output_dir);
      setProgress("gpc", 100, t("complete", { time: elapsed }));
      setResult("gpc", {
        success: true,
        message: "GPC analysis complete",
        data: result,
      });
      message.success(t("complete", { time: elapsed }));
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setResult("gpc", {
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
            checked={savePlotData}
            onChange={(e) => setSavePlotData(e.target.checked)}
          >
            {t("save_plot_data")}
          </Checkbox>
          <Checkbox
            checked={selectPartial}
            disabled={analyzer.running}
            onChange={(e) => setSelectPartial(e.target.checked)}
          >
            {t("select_partial_files")}
          </Checkbox>
        </div>
      </div>

      {/* File list — always visible, selection enabled when selectPartial */}
      <div className="panel-section">
        <label className="panel-section-title">{t("file_list")}</label>
        <Select
          mode="multiple"
          className="file-list-select"
          value={selectedFiles}
          onChange={setSelectedFiles}
          disabled={!selectPartial || analyzer.running}
          loading={filesLoading}
          options={fileList.map((f) => ({ label: f, value: f }))}
          placeholder={t("file_list")}
        />
        {fileError && <Alert type="error" showIcon message={fileError} />}
      </div>

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
          failed={analyzer.result?.success === false}
        />
      </div>
    </div>
  );
}
