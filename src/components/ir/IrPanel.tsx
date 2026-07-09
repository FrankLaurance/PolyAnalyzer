import { useEffect, useState } from "react";
import {
  Button,
  Checkbox,
  Collapse,
  ColorPicker,
  Input,
  InputNumber,
  Select,
  Slider,
  Space,
  Typography,
  message,
} from "antd";
import {
  FolderOpenOutlined,
  FolderViewOutlined,
  PlayCircleOutlined,
} from "@ant-design/icons";
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";
import { openPath } from "@tauri-apps/plugin-opener";
import { useTranslation } from "react-i18next";
import { usePythonBridge } from "../../hooks/usePythonBridge";
import { useAnalysisStore } from "../../stores/analysisStore";
import { useSettingsStore } from "../../stores/settingsStore";
import ProgressBar from "../common/ProgressBar";

interface IrAnalyzeResult {
  output_dir?: string;
  generated_files?: string[];
  processed_count?: number;
}

export default function IrPanel() {
  const { t } = useTranslation();
  const { sendRequest, lastProgress } = usePythonBridge();
  const analyzer = useAnalysisStore((s) => s.analyzers.ir);
  const { setRunning, setResult, setProgress, reset } = useAnalysisStore();
  const { analyzerSettings, updateAnalyzerSettings } = useSettingsStore();

  const [folderPath, setFolderPath] = useState("");
  const [fileList, setFileList] = useState<string[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [outputDir, setOutputDir] = useState("");
  const [generatedFiles, setGeneratedFiles] = useState<string[]>([]);
  const [processedCount, setProcessedCount] = useState(0);

  useEffect(() => {
    if (analyzer.running) {
      setProgress("ir", lastProgress.progress * 100, lastProgress.message);
    }
  }, [analyzer.running, lastProgress, setProgress]);

  useEffect(() => {
    sendRequest("system.get_default_ir_datapath", {}).then((res) => {
      const dp = (res as { datapath: string })?.datapath;
      if (dp) {
        setFolderPath(dp);
        loadFiles(dp);
      }
    }).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadFiles = async (path: string) => {
    try {
      const res = (await sendRequest("ir.list_files", {
        datadir: path,
      })) as { files: string[] };
      const files = res?.files ?? [];
      setFileList(files);
      setSelectedFiles(files);
    } catch (err) {
      setFileList([]);
      setSelectedFiles([]);
      message.error(err instanceof Error ? err.message : String(err));
    }
  };

  const handleBrowse = async () => {
    const selected = await open({ directory: true, multiple: false });
    if (selected) {
      const path = selected as string;
      setFolderPath(path);
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
    reset("ir");
    setRunning("ir", true);
    setGeneratedFiles([]);
    setProcessedCount(0);

    try {
      const result = await sendRequest("ir.analyze", {
        datadir: folderPath,
        selected_files: selectedFiles,
        curve_color: analyzerSettings.curveColor,
        line_width: analyzerSettings.lineWidth,
        axis_width: analyzerSettings.axisWidth,
        title_font_size: analyzerSettings.titleFontSize,
        axis_font_size: analyzerSettings.axisFontSize,
        transparent_back: analyzerSettings.transparentBackground,
      });
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      const res = result as IrAnalyzeResult;
      setOutputDir(res.output_dir ?? "");
      setGeneratedFiles(res.generated_files ?? []);
      setProcessedCount(res.processed_count ?? 0);
      setProgress("ir", 100, t("complete", { time: elapsed + "s" }));
      setResult("ir", {
        success: true,
        message: "IR analysis complete",
        data: result,
      });
      message.success(t("complete", { time: elapsed + "s" }));
    } catch (err) {
      setResult("ir", {
        success: false,
        message: err instanceof Error ? err.message : String(err),
      });
      message.error(String(err));
    }
  };

  const handleOpenFolder = async () => {
    const target = outputDir || folderPath;
    if (!target) return;
    try {
      await invoke("open_folder", { path: target });
    } catch {
      try { await openPath(target); } catch { /* ignore */ }
    }
  };

  return (
    <div className="panel-container">
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

      <div className="panel-section">
        <label className="panel-section-title">{t("ir_dpt_files")}</label>
        <Select
          mode="multiple"
          className="file-list-select"
          value={selectedFiles}
          onChange={setSelectedFiles}
          options={fileList.map((file) => ({ label: file, value: file }))}
          placeholder={t("file_list")}
        />
        {fileList.length === 0 && (
          <Typography.Text type="secondary">{t("ir_no_dpt_files")}</Typography.Text>
        )}
      </div>

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
                      updateAnalyzerSettings({
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
                    onChange={(color) =>
                      updateAnalyzerSettings({ curveColor: color.toHexString() })
                    }
                  />
                </div>

                <div className="slider-row">
                  <label>{t("line_width")}:</label>
                  <Slider
                    min={0.2}
                    max={3}
                    step={0.1}
                    value={analyzerSettings.lineWidth}
                    onChange={(value) => updateAnalyzerSettings({ lineWidth: value })}
                  />
                  <span style={{ minWidth: 36 }}>{analyzerSettings.lineWidth}</span>
                </div>

                <div className="slider-row">
                  <label>{t("axis_width")}:</label>
                  <Slider
                    min={0.5}
                    max={3}
                    step={0.1}
                    value={analyzerSettings.axisWidth}
                    onChange={(value) => updateAnalyzerSettings({ axisWidth: value })}
                  />
                  <span style={{ minWidth: 36 }}>{analyzerSettings.axisWidth}</span>
                </div>

                <div className="panel-row">
                  <label style={{ minWidth: 140, textAlign: "right" }}>{t("title_font_size")}:</label>
                  <InputNumber
                    min={8}
                    max={48}
                    value={analyzerSettings.titleFontSize}
                    onChange={(value) =>
                      updateAnalyzerSettings({ titleFontSize: value ?? analyzerSettings.titleFontSize })
                    }
                  />
                  <label style={{ minWidth: 140, textAlign: "right" }}>{t("axis_font_size")}:</label>
                  <InputNumber
                    min={8}
                    max={36}
                    value={analyzerSettings.axisFontSize}
                    onChange={(value) =>
                      updateAnalyzerSettings({ axisFontSize: value ?? analyzerSettings.axisFontSize })
                    }
                  />
                </div>
              </div>
            ),
          },
        ]}
      />

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

      {outputDir && (
        <div className="panel-section">
          <Typography.Text strong>{t("ir_output_folder")}:</Typography.Text>
          <Typography.Paragraph copyable>{outputDir}</Typography.Paragraph>
          <Typography.Text>
            {t("ir_processed_count", { count: processedCount })} · {t("ir_generated_files", { count: generatedFiles.length })}
          </Typography.Text>
        </div>
      )}
    </div>
  );
}
