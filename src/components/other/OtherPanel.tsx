import { useState } from "react";
import { Button, Input, Checkbox, Popconfirm, Space, message } from "antd";
import {
  FolderOpenOutlined,
  ClearOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { open } from "@tauri-apps/plugin-dialog";
import { usePythonBridge } from "../../hooks/usePythonBridge";

export default function OtherPanel() {
  const { t } = useTranslation();
  const { sendRequest } = usePythonBridge();

  const [folderPath, setFolderPath] = useState("");
  const [cleanFolder, setCleanFolder] = useState(false);
  const [cleaning, setCleaning] = useState(false);

  const handleBrowse = async () => {
    const selected = await open({ directory: true, multiple: false });
    if (selected) {
      setFolderPath(selected as string);
    }
  };

  const handleClean = async () => {
    if (!folderPath) {
      message.warning(t("invalid_path"));
      return;
    }
    setCleaning(true);
    try {
      await sendRequest("clean_folder", { folder: folderPath });
      message.success(t("clean_success"));
    } catch (err) {
      message.error(String(err));
    } finally {
      setCleaning(false);
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
            placeholder={t("data_folder")}
          />
          <Button icon={<FolderOpenOutlined />} onClick={handleBrowse}>
            {t("open_folder")}
          </Button>
        </div>
      </div>

      <div className="panel-section">
        <Space direction="vertical" size="middle">
          <Checkbox
            checked={cleanFolder}
            onChange={(e) => setCleanFolder(e.target.checked)}
          >
            {t("clean_folder")}
          </Checkbox>
          <Popconfirm
            title={t("confirm")}
            description={t("clean_folder")}
            onConfirm={handleClean}
            okText={t("confirm")}
            cancelText={t("cancel")}
            disabled={!cleanFolder}
          >
            <Button
              danger
              icon={<ClearOutlined />}
              disabled={!cleanFolder}
              loading={cleaning}
            >
              {t("run_clean")}
            </Button>
          </Popconfirm>
        </Space>
      </div>
    </div>
  );
}
