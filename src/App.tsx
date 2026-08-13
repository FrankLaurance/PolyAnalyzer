import { lazy, Suspense, useState } from "react";
import { Alert, Button, Tabs, Layout, Spin, Typography } from "antd";
import { useTranslation } from "react-i18next";
import { WebviewWindow } from "@tauri-apps/api/webviewWindow";
import Header from "./components/layout/Header";
import { usePythonBridge } from "./hooks/usePythonBridge";
import "./App.css";

const GpcPanel = lazy(() => import("./components/gpc/GpcPanel"));
const MwPanel = lazy(() => import("./components/mw/MwPanel"));
const DscPanel = lazy(() => import("./components/dsc/DscPanel"));
const IrPanel = lazy(() => import("./components/ir/IrPanel"));
const OtherPanel = lazy(() => import("./components/other/OtherPanel"));

const { Content, Sider } = Layout;
const { Paragraph } = Typography;

const panelFallback = <div className="panel-loading"><Spin /></div>;

async function openManualWindow(title: string) {
  try {
    const existing = await WebviewWindow.getByLabel("manual");
    if (existing) {
      await existing.setFocus();
      return;
    }
    await new WebviewWindow("manual", {
      url: "manual.html",
      title,
      width: 960,
      height: 720,
      minWidth: 640,
      minHeight: 480,
    });
  } catch (error) {
    console.error("[manual-window] failed to open:", error);
    // Not running inside Tauri (plain browser dev) — fall back to a new tab.
    window.open("manual.html", "_blank");
  }
}

function App() {
  const { t } = useTranslation();
  const { engineStatus } = usePythonBridge("system");
  const [activeTab, setActiveTab] = useState("gpc");

  const tabItems = [
    { key: "gpc", label: t("tab_gpc"), children: <Suspense fallback={panelFallback}><GpcPanel /></Suspense> },
    { key: "mw", label: t("tab_mw"), children: <Suspense fallback={panelFallback}><MwPanel /></Suspense> },
    { key: "dsc", label: t("tab_dsc"), children: <Suspense fallback={panelFallback}><DscPanel /></Suspense> },
    { key: "ir", label: t("tab_ir"), children: <Suspense fallback={panelFallback}><IrPanel /></Suspense> },
    { key: "other", label: t("tab_other"), children: <Suspense fallback={panelFallback}><OtherPanel /></Suspense> },
  ];

  return (
    <Layout className="app-layout">
      <Header />
      <Layout className="app-body">
        <Content className="app-content">
          {engineStatus === "warming" && (
            <Alert
              className="engine-warmup-banner"
              type="info"
              showIcon
              message={t("engine_warming")}
            />
          )}
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
            type="card"
            size="large"
            destroyOnHidden={false}
          />
        </Content>
        <Sider className="app-sider" width={240} theme="light" style={{ background: 'var(--color-surface)' }}>
          <div className="help-panel">
            <Typography.Title level={5}>{t("help")}</Typography.Title>
            <Paragraph type="secondary">{t("contact_info")}</Paragraph>
            <Button
              type="primary"
              onClick={() => void openManualWindow(t("manual"))}
            >
              {t("manual")}
            </Button>
          </div>
        </Sider>
      </Layout>
    </Layout>
  );
}

export default App;
