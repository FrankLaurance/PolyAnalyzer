import { useState } from "react";
import { Select, Button, Input, Popconfirm, Space } from "antd";
import { SaveOutlined, DeleteOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";

interface SettingsPanelProps {
  settingsList: string[];
  currentSetting?: string;
  onSwitch: (name: string) => void;
  onSave: (name: string) => void;
  onDelete: (name: string) => void;
}

export default function SettingsPanel({
  settingsList,
  currentSetting,
  onSwitch,
  onSave,
  onDelete,
}: SettingsPanelProps) {
  const { t } = useTranslation();
  const [newName, setNewName] = useState("");

  const handleSave = () => {
    const name = newName.trim();
    if (name) {
      onSave(name);
      setNewName("");
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        <label>{t("settings_list")}</label>
        <Select
          style={{ width: "100%", marginTop: 4 }}
          value={currentSetting}
          onChange={onSwitch}
          placeholder={t("switch_setting")}
          options={settingsList.map((s) => ({ label: s, value: s }))}
          allowClear
        />
      </div>
      <Space.Compact style={{ width: "100%", marginBottom: 12 }}>
        <Input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder={t("setting_name")}
          onPressEnter={handleSave}
        />
        <Button icon={<SaveOutlined />} onClick={handleSave}>
          {t("save_setting")}
        </Button>
      </Space.Compact>
      {currentSetting && (
        <Popconfirm
          title={t("delete_setting")}
          onConfirm={() => onDelete(currentSetting)}
          okText={t("confirm")}
          cancelText={t("cancel")}
        >
          <Button danger icon={<DeleteOutlined />}>
            {t("delete_setting")}
          </Button>
        </Popconfirm>
      )}
    </div>
  );
}
