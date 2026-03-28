import { useState } from "react";
import { Tabs, Layout, Typography } from "antd";
import { useTranslation } from "react-i18next";
import Header from "./components/layout/Header";
import GpcPanel from "./components/gpc/GpcPanel";
import MwPanel from "./components/mw/MwPanel";
import DscPanel from "./components/dsc/DscPanel";
import OtherPanel from "./components/other/OtherPanel";
import "./App.css";

const { Content, Sider } = Layout;
const { Paragraph } = Typography;

function App() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("gpc");

  const tabItems = [
    { key: "gpc", label: t("tab_gpc"), children: <GpcPanel /> },
    { key: "mw", label: t("tab_mw"), children: <MwPanel /> },
    { key: "dsc", label: t("tab_dsc"), children: <DscPanel /> },
    { key: "other", label: t("tab_other"), children: <OtherPanel /> },
  ];

  return (
    <Layout className="app-layout">
      <Header />
      <Layout className="app-body">
        <Content className="app-content">
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
            type="card"
            size="large"
          />
        </Content>
        <Sider className="app-sider" width={240} theme="light" style={{ background: 'var(--color-surface)' }}>
          <div className="help-panel">
            <Typography.Title level={5}>{t("help")}</Typography.Title>
            <Paragraph type="secondary">{t("contact_info")}</Paragraph>
          </div>
        </Sider>
      </Layout>
    </Layout>
  );
}

export default App;
