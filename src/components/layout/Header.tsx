import { Select, Typography, Tag } from "antd";
import { GlobalOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { useSettingsStore } from "../../stores/settingsStore";
import { getVersion } from "@tauri-apps/api/app";
import { useState, useEffect } from "react";

export default function Header() {
  const { t } = useTranslation();
  const { language, setLanguage } = useSettingsStore();
  const [version, setVersion] = useState("");

  useEffect(() => {
    getVersion().then(setVersion).catch(() => {});
  }, []);

  return (
    <header className="app-header">
      <div className="app-header-left">
        <Typography.Title level={4} className="app-header-title">
          {t("app_title")}
        </Typography.Title>
        {version && <Tag color="blue">v{version}</Tag>}
      </div>
      <div className="app-header-right">
        <GlobalOutlined />
        <Select
          value={language}
          onChange={setLanguage}
          style={{ width: 120 }}
          options={[
            { label: "中文", value: "zh_CN" },
            { label: "English", value: "en_US" },
          ]}
        />
      </div>
    </header>
  );
}
