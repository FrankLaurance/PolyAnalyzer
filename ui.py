"""
UI模块 - 负责Streamlit界面的渲染和交互
"""

import streamlit as st
import os
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import MolecularWeightAnalyzer, GPCAnalyzer

# 全局变量
start_time = time.time()


def open_folder(path: str) -> None:
    """跨平台打开文件夹
    
    Args:
        path: 文件夹路径
    """
    import platform
    import subprocess
    
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path])
        elif platform.system() == "Linux":
            subprocess.run(["xdg-open", path])
        else:
            st.warning("不支持的操作系统")
    except Exception as e:
        st.error(f"无法打开文件夹: {e}")


def render_mw_settings(mw: 'MolecularWeightAnalyzer') -> None:
    """渲染分子量分析器的设置界面
    
    Args:
        mw: 分子量分析器实例
    """
    picSet = st.expander("画图设置")
   
    with picSet:
        barColor_col, MwColor_col, transparentBack_col, drawBar_col, drawMw_col, drawTable_col, settingList_col, deleteSetting_col, *_ = st.columns(spec=8)
        barWidth_col, lineWidth_col, axisWidth_col, titleFontSize_col, axisFontSize_col, switchSetting_col, settingname_col, saveSetting_col, *_ = st.columns(spec=8)
        
        # 第一行：颜色和绘图选项
        mw.bar_color = barColor_col.color_picker("柱状图颜色选择", value=mw.bar_color, key="barColor_col")
        mw.mw_color = MwColor_col.color_picker("分子量分布颜色选择", value=mw.mw_color, key="MwColor_col")
        mw.transparent_back = transparentBack_col.checkbox("透明背景", value=mw.transparent_back, key="transparentBack_col")
        mw.draw_bar = drawBar_col.checkbox("绘制柱状图", value=mw.draw_bar, key="drawBar_col")
        mw.draw_mw = drawMw_col.checkbox("绘制Mw曲线", value=mw.draw_mw, key="drawMw_col")
        mw.draw_table = drawTable_col.checkbox("绘制表格", value=mw.draw_table, key="drawTable_col")
        mw.setting_name = settingList_col.selectbox("设置列表", mw.setting_list(), key="settingList_col")
        deleteSetting_col.button("删除设置", key="deleteSetting_col", on_click=mw.delete_setting, args=[mw.setting_name])
        
        # 第二行：尺寸和字体调整
        mw.bar_width = barWidth_col.slider("柱状图宽度", key="barWidth_col", min_value=0.2, max_value=2.0, step=0.1, value=mw.bar_width)
        mw.line_width = lineWidth_col.slider("Mw曲线宽度", key="lineWidth_col", min_value=0.2, max_value=2.0, step=0.1, value=mw.line_width)
        mw.axis_width = axisWidth_col.slider("坐标轴宽度", key="axisWidth_col", min_value=0.5, max_value=2.0, step=0.1, value=mw.axis_width)
        mw.title_font_size = titleFontSize_col.slider("标题字号", key="titleFontSize_col", min_value=14, max_value=28, step=1, value=mw.title_font_size)
        mw.axis_font_size = axisFontSize_col.slider("坐标标题字号", key="axisFontSize_col", min_value=10, max_value=18, step=1, value=mw.axis_font_size)
        switchSetting_col.button("切换设置", key="switchSetting_col", on_click=mw.change_setting, args=[mw.setting_name])
        newsettingname = settingname_col.text_input("设置名称", key="saveRegion_col", value=mw.setting_name)
        saveSetting_col.button("保存设置", key="saveSetting_col", on_click=mw.save_setting, args=[newsettingname], disabled=(mw.setting_name == newsettingname))


def render_mw_region_settings(mw: 'MolecularWeightAnalyzer') -> None:
    """渲染分子量区域设置界面
    
    Args:
        mw: 分子量分析器实例
    """
    rangeSet = st.expander("区域设置")

    with rangeSet:
        selectedRegion = st.multiselect("分割位置", mw.segmentpos, default=mw.selectedpos)
        selectedRegion.sort()
        mw.selectedpos = selectedRegion
        
        new_region_col, addRegion_col, *_ = st.columns(spec=6)
        new_region = new_region_col.number_input("新分割位置", min_value=0, max_value=1000000000)
        addRegion_col.button("添加", key="addRegion_col", on_click=mw.add_region, args=[new_region])
        mw.selected_file = st.multiselect("文件列表", mw.read_file_list(), default=mw.read_file_list())


def render_mw_ui(default_dir: str) -> None:
    """渲染分子量分析UI标签页
    
    Args:
        default_dir: 默认数据目录
    """
    from main import MolecularWeightAnalyzer
    
    datapath_mw = st.text_input("数据文件夹", value=default_dir, max_chars=100, key="datapath_mw")
    if not os.path.isdir(datapath_mw):
        st.warning("请输入正确路径")

    savePic_mw_col, displayPic_mw_col, *_ = st.columns(spec=8)
    savePic_mw = savePic_mw_col.checkbox("保存图像", value=True, key="savePic_mw_col")
    displayPic_mw = displayPic_mw_col.checkbox("显示图片", value=False, key="displayPic_mw_col")
    
    st.empty()  # output_filename_mw_col
    st.empty()  # fileSelect_mw_col
    
    # 初始化进度条
    progressBar_mw = st.empty()
    
    # 定义进度回调函数
    def progress_callback(progress: float, text: str):
        progressBar_mw.progress(progress, text)
                
    mw = MolecularWeightAnalyzer(datapath_mw, save_picture=savePic_mw, display_picture=displayPic_mw, 
                                  test_mode=False, progress_callback=progress_callback)
    
    # 画图设置
    render_mw_settings(mw)
    
    # 区域设置
    render_mw_region_settings(mw)
    
    # 运行控制
    run_mw_col, openDir_mw_col, infoBar_mw_col, *_ = st.columns(spec=8)
    
    overlayFile_mw = True
    if mw.check_dir():
        overlayFile_mw = st.checkbox("确认覆盖", key="overlayFile_mw_col")
        if not overlayFile_mw:
            st.warning("存在相同文件名文件")

    if run_mw_col.button("运行", key="run_mw_col_mw", disabled=not overlayFile_mw):
        infoBar_mw = infoBar_mw_col.empty()
        result_mw = mw.run()
        infoBar_mw.text("完成！耗时{:.2f}s".format(time.time() - start_time))

    if os.path.isdir(datapath_mw):
        if openDir_mw_col.button("打开目标文件夹", key="openDir_mw_col_mw"):
            open_folder(mw.output_dir)


def render_gpc_ui(default_dir: str) -> None:
    """渲染GPC分析UI标签页
    
    Args:
        default_dir: 默认数据目录
    """
    from main import GPCAnalyzer
    
    datapath_gpc = st.text_input("数据文件夹", value=default_dir, max_chars=100, key="datapath_gpc")
    if not os.path.isdir(datapath_gpc):
        st.warning("请输入正确路径")

    save_file_col, save_picture_col, display_mode_col, save_figure_file_gpc_col, selected_gpc_col, draw_mw_col, *_ = st.columns(spec=8)
    save_file = save_file_col.checkbox("保存样品信息", value=True)
    save_picture = save_picture_col.checkbox("保存图像", value=True)
    display_mode = display_mode_col.checkbox("显示图像", value=True)
    save_figure_file_gpc = save_figure_file_gpc_col.checkbox("保存画图数据", value=False)
    selected = selected_gpc_col.checkbox("选择部分文件")

    output_filename = st.text_input("输出文件名", value=time.strftime("%Y%m%d", time.localtime()), max_chars=100, key="output_filename", disabled=not (save_file or save_picture))
    overlayFile_col = st.empty()
    fileSelect_col = st.empty()
    run_gpc_col, openDir_gpc_col, infoBar_gpc_col, *_ = st.columns(spec=8)
    
    # 初始化进度条和信息栏
    progressBar_gpc = st.empty()
    infoBar_gpc = st.empty()
    
    # 定义回调函数
    def progress_callback(progress: float, text: str):
        progressBar_gpc.progress(progress, text)
    
    def info_callback(text: str):
        infoBar_gpc.text(text)
    
    gpc = GPCAnalyzer(datapath_gpc, output_filename, save_file, save_picture, display_mode, 
                      save_figure_file_gpc, test_mode=False, 
                      progress_callback=progress_callback, info_callback=info_callback)

    if selected:
        gpc.selected_file = fileSelect_col.multiselect("文件列表", gpc.read_file_list())
        
    overlayFile = True
    if gpc.check_dir():
        overlayFile = overlayFile_col.checkbox("确认覆盖")
        if not overlayFile:
            st.warning("存在相同文件名文件")  

    if run_gpc_col.button("运行", key="run_gpc_col", disabled=not overlayFile):
        infoBar_gpc = infoBar_gpc_col.empty()
        result_gpc = gpc.run()
        infoBar_gpc.text("完成！耗时{:.2f}s".format(time.time() - start_time))

    if os.path.isdir(datapath_gpc):
        if openDir_gpc_col.button("打开目标文件夹", key="openDir_gpc_col"):
            open_folder(gpc.output_dir)


def render_other_ui(default_dir: str) -> None:
    """渲染其他功能UI标签页
    
    Args:
        default_dir: 默认数据目录
    """
    datapath_other = st.text_input("数据文件夹", value=default_dir, max_chars=100, key="datapath_other")
    if os.path.isdir(datapath_other):
        clear_confirm = st.checkbox("清理文件夹", value=False)
    else:
        st.warning("请输入正确路径")


def render_sidebar() -> None:
    """渲染侧边栏"""
    with st.sidebar:
        with st.expander("帮助", expanded=True):
            st.markdown('''Tel: 13716441322               
                         Email: liuzhen.bjhy@sinopec.com''')


def render_app() -> None:
    """渲染完整的应用UI"""
    # 配置页面
    st.set_page_config(
        page_title='GPC_PAGE',
        page_icon='',
        layout='wide',
        initial_sidebar_state="collapsed"
    )
    
    # 默认数据目录
    default_dir = os.path.join(os.getcwd(), "datapath")
    
    # 创建标签页
    Mw_ui, gpc_ui, other_ui = st.tabs(["Mw", "GPC", "Other"])
    
    with Mw_ui:
        render_mw_ui(default_dir)
    
    with gpc_ui:
        render_gpc_ui(default_dir)
    
    with other_ui:
        render_other_ui(default_dir)
    
    # 渲染侧边栏
    render_sidebar()


# 导出全局变量供main.py使用
__all__ = ['render_app', 'progressBar_mw', 'infoBar_mw', 'progressBar_gpc', 'infoBar_gpc', 'start_time']

# 这些变量需要在main.py中访问
progressBar_mw = None
infoBar_mw = None
progressBar_gpc = None
infoBar_gpc = None
