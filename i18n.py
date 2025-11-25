"""
国际化模块 (i18n) - 多语言支持
支持中文(简体)和英语
"""

import json
import os
from typing import Dict, Any

# 语言配置
LANGUAGES = {
    "zh_CN": "中文(简体)",
    "en_US": "English"
}

# 翻译字典
TRANSLATIONS = {
    "zh_CN": {
        # 通用
        "app_title": "GPC数据可视化工具",
        "language": "语言",
        "save": "保存",
        "cancel": "取消",
        "confirm": "确认",
        "delete": "删除",
        "add": "添加",
        "run": "运行",
        "open_folder": "打开目标文件夹",
        "help": "帮助",
        "settings": "设置",
        "complete": "完成！耗时{:.2f}s",
        
        # 标签页
        "tab_mw": "Mw",
        "tab_gpc": "GPC",
        "tab_other": "其他",
        
        # 文件和路径
        "data_folder": "数据文件夹",
        "output_filename": "输出文件名",
        "file_list": "文件列表",
        "invalid_path": "请输入正确路径",
        "confirm_overwrite": "确认覆盖",
        "file_exists_warning": "存在相同文件名文件",
        "select_partial_files": "选择部分文件",
        
        # 图像设置
        "plot_settings": "画图设置",
        "bar_color": "柱状图颜色选择",
        "mw_color": "分子量分布颜色选择",
        "transparent_background": "透明背景",
        "draw_bar": "绘制柱状图",
        "draw_mw": "绘制Mw曲线",
        "draw_table": "绘制表格",
        "bar_width": "柱状图宽度",
        "line_width": "Mw曲线宽度",
        "axis_width": "坐标轴宽度",
        "title_font_size": "标题字号",
        "axis_font_size": "坐标标题字号",
        
        # 设置管理
        "settings_list": "设置列表",
        "delete_setting": "删除设置",
        "switch_setting": "切换设置",
        "setting_name": "设置名称",
        "save_setting": "保存设置",
        
        # 区域设置
        "region_settings": "区域设置",
        "split_position": "分割位置",
        "new_split_position": "新分割位置",
        "add_region": "添加",
        
        # 保存选项
        "save_image": "保存图像",
        "display_image": "显示图片",
        "save_sample_info": "保存样品信息",
        "save_plot_data": "保存画图数据",
        
        # 其他功能
        "clean_folder": "清理文件夹",
        "unsupported_os": "不支持的操作系统",
        "cannot_open_folder": "无法打开文件夹: {}",
        
        # 联系信息
        "contact_info": "GitHub: https://github.com/FrankLaurance/GPCtoPic",
    },
    
    "en_US": {
        # Common
        "app_title": "GPC Data Visualization Tool",
        "language": "Language",
        "save": "Save",
        "cancel": "Cancel",
        "confirm": "Confirm",
        "delete": "Delete",
        "add": "Add",
        "run": "Run",
        "open_folder": "Open Output Folder",
        "help": "Help",
        "settings": "Settings",
        "complete": "Complete! Time elapsed: {:.2f}s",
        
        # Tabs
        "tab_mw": "Mw",
        "tab_gpc": "GPC",
        "tab_other": "Other",
        
        # Files and Paths
        "data_folder": "Data Folder",
        "output_filename": "Output Filename",
        "file_list": "File List",
        "invalid_path": "Please enter a valid path",
        "confirm_overwrite": "Confirm Overwrite",
        "file_exists_warning": "File with same name exists",
        "select_partial_files": "Select Partial Files",
        
        # Plot Settings
        "plot_settings": "Plot Settings",
        "bar_color": "Bar Chart Color",
        "mw_color": "Molecular Weight Color",
        "transparent_background": "Transparent Background",
        "draw_bar": "Draw Bar Chart",
        "draw_mw": "Draw Mw Curve",
        "draw_table": "Draw Table",
        "bar_width": "Bar Width",
        "line_width": "Mw Curve Width",
        "axis_width": "Axis Width",
        "title_font_size": "Title Font Size",
        "axis_font_size": "Axis Font Size",
        
        # Settings Management
        "settings_list": "Settings List",
        "delete_setting": "Delete Setting",
        "switch_setting": "Switch Setting",
        "setting_name": "Setting Name",
        "save_setting": "Save Setting",
        
        # Region Settings
        "region_settings": "Region Settings",
        "split_position": "Split Position",
        "new_split_position": "New Split Position",
        "add_region": "Add",
        
        # Save Options
        "save_image": "Save Image",
        "display_image": "Display Image",
        "save_sample_info": "Save Sample Info",
        "save_plot_data": "Save Plot Data",
        
        # Other Functions
        "clean_folder": "Clean Folder",
        "unsupported_os": "Unsupported Operating System",
        "cannot_open_folder": "Cannot open folder: {}",
        
        # Contact Info
        "contact_info": "GitHub: https://github.com/FrankLaurance/GPCtoPic",
    }
}


class I18n:
    """国际化类"""
    
    def __init__(self, default_language: str = "zh_CN"):
        """初始化
        
        Args:
            default_language: 默认语言代码
        """
        self.current_language = default_language
        self._load_language_preference()
    
    def _load_language_preference(self) -> None:
        """从配置文件加载语言偏好"""
        config_file = os.path.join("setting", "language.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_language = config.get("language", self.current_language)
            except Exception:
                pass
    
    def _save_language_preference(self) -> None:
        """保存语言偏好到配置文件"""
        config_file = os.path.join("setting", "language.json")
        os.makedirs("setting", exist_ok=True)
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({"language": self.current_language}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def set_language(self, language_code: str) -> None:
        """设置当前语言
        
        Args:
            language_code: 语言代码 (zh_CN 或 en_US)
        """
        if language_code in LANGUAGES:
            self.current_language = language_code
            self._save_language_preference()
    
    def get_language(self) -> str:
        """获取当前语言代码
        
        Returns:
            当前语言代码
        """
        return self.current_language
    
    def get_language_name(self) -> str:
        """获取当前语言名称
        
        Returns:
            当前语言显示名称
        """
        return LANGUAGES.get(self.current_language, "Unknown")
    
    def t(self, key: str, *args, **kwargs) -> str:
        """翻译函数
        
        Args:
            key: 翻译键
            *args: 格式化参数
            **kwargs: 格式化关键字参数
            
        Returns:
            翻译后的文本
        """
        translations = TRANSLATIONS.get(self.current_language, TRANSLATIONS["zh_CN"])
        text = translations.get(key, key)
        
        # 支持格式化
        if args or kwargs:
            try:
                text = text.format(*args, **kwargs)
            except (KeyError, IndexError):
                pass
        
        return text
    
    def get_available_languages(self) -> Dict[str, str]:
        """获取所有可用语言
        
        Returns:
            语言代码到显示名称的字典
        """
        return LANGUAGES.copy()


# 全局实例
_i18n_instance = None

def get_i18n() -> I18n:
    """获取全局i18n实例
    
    Returns:
        I18n实例
    """
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18n()
    return _i18n_instance


def t(key: str, *args, **kwargs) -> str:
    """便捷翻译函数
    
    Args:
        key: 翻译键
        *args: 格式化参数
        **kwargs: 格式化关键字参数
        
    Returns:
        翻译后的文本
    """
    return get_i18n().t(key, *args, **kwargs)
