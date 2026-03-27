import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import zhCN from "./zh_CN.json";
import enUS from "./en_US.json";

i18n.use(initReactI18next).init({
  resources: {
    zh_CN: { translation: zhCN },
    en_US: { translation: enUS },
  },
  lng: localStorage.getItem("polyanalyzer-language") || "zh_CN",
  fallbackLng: "zh_CN",
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
