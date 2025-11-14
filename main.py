import streamlit as st
import os
import time
import numpy as np
# matplotlib 和 plottable 改为延迟加载,减少 PyInstaller 打包体积
# import matplotlib.pyplot as plt
# import matplotlib.gridspec as gridspec
# from plottable import Table, ColumnDefinition
import glob
import pandas as pd
from typing import List
import platform
import subprocess

# 设置 matplotlib 后端为 Agg (非交互式),减少依赖
os.environ['MPLBACKEND'] = 'Agg'

# 常量定义
DEFAULT_BAR_COLOR = "#002FA7"
DEFAULT_MW_COLOR = "#FF6A07"
DEFAULT_SETTING_NAME = "defaultSetting.ini"
DEFAULT_TRANSPARENT_BACK = True

def open_folder(path):
    """跨平台打开文件夹"""
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

start_time = time.time()
st.set_page_config(
    page_title='PPR_DATA_PAGE',
    page_icon='sinopec.jpg',
    layout='wide',
    initial_sidebar_state = "collapsed"
)

class MolecularWeightAnalyzer():
    def __init__(self, datadir : str, save_file : bool = True, bar_width : float = 1.2, line_width : float = 1.0, axis_width : float = 1.0,
                 title_font_size : float = 20, axis_font_size : float = 14, transparent_back = DEFAULT_TRANSPARENT_BACK, save_picture : bool = True, display_picture : bool = False, 
                 bar_color : str = DEFAULT_BAR_COLOR, mw_color : str = DEFAULT_MW_COLOR, draw_bar : bool = True, draw_mw : bool = True, draw_table : bool = True, 
                 setting_name : str = DEFAULT_SETTING_NAME, test_mode = False):
        # 使用当前脚本所在目录作为根目录，确保配置文件在当前目录下
        self.rootdir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(self.rootdir, "datapath")
        self.output_dir = os.path.join(self.rootdir, "Mw_output")
        self.setting_dir = os.path.join(self.rootdir, "setting")
        self.file_list : List[str] = None
        # self.heads = {}  # 变量名
        self.lines = []  # raw data 读文件用
        self.selected_file = None
        
        # 每个文件的数据存储
        self.filename = ""
        self.sample_name = ""
        self.mw_data = []  # Mw 数据
        self.peak_num = 0  # 峰数目
        self.peak_pos = [] # 峰 数据位置
        self.peak_data = {}        
        self.norm = None
        self.mw = None


        # 画图设置
        self.setting_name = setting_name
        if "settingname" not in st.session_state:
            self.setting_name = setting_name
            st.session_state["settingname"] = self.setting_name
        else:
            self.setting_name = st.session_state["settingname"]
        # print(self.setting_name)
        
        if not os.path.exists(self.setting_dir):
            os.makedirs(self.setting_dir, exist_ok=True)
        
        if os.path.exists(os.path.join(self.setting_dir, self.setting_name)):
            setting = self.read_setting()
        else:
            setting = self.default_setting()
                    
        if "segmentpos" not in st.session_state:
            self.segmentpos = setting["segmentpos"]
            st.session_state["segmentpos"] = self.segmentpos
        else:
            self.segmentpos = st.session_state["segmentpos"]
        if "selectedpos" not in st.session_state:
            self.selectedpos = self.segmentpos
            st.session_state["selectedpos"] = self.segmentpos
        else:
            self.selectedpos = st.session_state["selectedpos"]
        self.segmentnum = len(self.segmentpos)

        # 运行模式
        self.test_mode = test_mode
        self.save_file = save_file
        self.save_picture = save_picture
        self.display_picture = display_picture
          
    def reset(self):
        """重置所有数据属性"""
        self.lines = []
        self.mw_data = []
        self.filename = ""
        self.sample_name = ""
        self.peak_num = 0
        self.peak_pos = []
        self.peak_data = {}
        self.norm = None
        self.mw = None

    def clear_dir(self):
        if not os.path.exists(self.output_dir):
            return
        for dir in os.listdir(self.output_dir):
            os.remove(os.path.join(self.output_dir, dir))

    def check_dir(self) -> bool:
        """检查输出目录中是否存在同名文件"""
        for file in self.selected_file:
            if os.path.exists(os.path.join(self.output_dir, file.split('.')[0] + '.png')):
                return True
        return False    

    def setting_list(self):
        return [os.path.basename(i) for i in glob.glob(os.path.join(self.setting_dir, "*.ini"))]

    def save_setting(self, new_setting_name = '') -> None:
        """保存当前设置到文件"""
        with open(os.path.join(self.setting_dir, new_setting_name), 'w') as f:
            setting = {"segmentpos": self.selectedpos,
                        "bar_color" : self.bar_color,
                        "mw_color" : self.mw_color,
                        "transparent_back" : self.transparent_back,
                        "bar_width" : self.bar_width,
                        "line_width" : self.line_width,
                        "axis_width" : self.axis_width,
                        "title_font_size" : self.title_font_size,
                        "axis_font_size" : self.axis_font_size,
                        "draw_bar" : self.draw_bar,
                        "draw_mw" : self.draw_mw,
                        "draw_table" : self.draw_table}
                
            print(setting, end = '', file = f)
            st.session_state["segmentpos"] = self.selectedpos
            st.session_state["selectedpos"] = self.selectedpos
                        
    def delete_setting(self, settingname):
        """删除指定的设置文件"""
        os.remove(os.path.join(self.setting_dir, settingname))
        if len(os.listdir(self.setting_dir)) == 0:
            self.default_setting()
            
    def default_setting(self):
        setting_name = DEFAULT_SETTING_NAME
        st.session_state["settingname"] = self.setting_name
        bar_color = DEFAULT_BAR_COLOR
        mw_color = DEFAULT_MW_COLOR
        bar_width = 1.2
        line_width = 1.0
        axis_width = 1.0
        title_font_size = 20
        axis_font_size = 14
        draw_bar = True
        draw_mw = True
        draw_table = True
        transparent_back = DEFAULT_TRANSPARENT_BACK
        segmentpos = [0, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000, 10000000]
        st.session_state["segmentpos"] = segmentpos
        st.session_state["selectedpos"] = segmentpos
        
        with open(os.path.join(self.setting_dir, setting_name), 'w') as f:
                segmentpos = [0, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000, 10000000, 50000000]
                setting = {"segmentpos": segmentpos,
                           "barColor" : bar_color,
                            "MwColor" : mw_color,
                            "transparentBack" : transparent_back,
                            "barWidth" : bar_width,
                            "lineWidth" : line_width,
                            "axisWidth" : axis_width,
                            "titleFontSize" : title_font_size,
                            "axisFontSize" : axis_font_size,
                            "drawBar" : draw_bar,
                            "drawMw" : draw_mw,
                            "drawTable" : draw_table}
                print(setting, end = '', file = f)
        return setting
        
    def read_setting(self, settingname = '') -> dict:
        """读取设置文件，兼容旧键名和新键名"""
        if os.path.exists(os.path.join(self.setting_dir, self.setting_name)):
            with open(os.path.join(self.setting_dir, self.setting_name)) as f:
                setting = eval(f.read())
            # 兼容旧键名（驼峰）和新键名（下划线）
            self.bar_color = setting.get("bar_color", setting.get("barColor", DEFAULT_BAR_COLOR))
            self.mw_color = setting.get("mw_color", setting.get("MwColor", DEFAULT_MW_COLOR))
            self.bar_width = setting.get("bar_width", setting.get("barWidth", 1.2))
            self.line_width = setting.get("line_width", setting.get("lineWidth", 1.0))
            self.axis_width = setting.get("axis_width", setting.get("axisWidth", 1.0))
            self.title_font_size = setting.get("title_font_size", setting.get("titleFontSize", 20))
            self.axis_font_size = setting.get("axis_font_size", setting.get("axisFontSize", 14))
            self.draw_bar = setting.get("draw_bar", setting.get("drawBar", True))
            self.draw_mw = setting.get("draw_mw", setting.get("drawMw", True))
            self.draw_table = setting.get("draw_table", setting.get("drawTable", True))
            self.transparent_back = setting.get("transparent_back", setting.get("transparentBack", DEFAULT_TRANSPARENT_BACK))
        else:
            os.makedirs(self.setting_dir, exist_ok=True)
            setting = self.default_setting()
        return setting
    
    def change_setting(self, settingname):
        """切换到指定的设置"""
        st.session_state["settingname"] = self.setting_name
        return

    def add_region(self, new_region):
        # print(new_region, type(new_region))
        self.segmentpos.append(new_region)
        self.segmentpos.sort()
    
    def read_file(self, name):
        self.reset()
        file_path = os.path.join(self.data_path, name)
        with open(file_path, "r", newline="", encoding = "ascii") as file:
            # print(chardet.detect(file.read()))
            for line in file.readlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                self.lines.append(line)
            return True
        return False
        
    def preprocess(self):
        """预处理数据文件，提取分子量和峰数据"""
        mw_start = 0
        mw_end = 0
        slice_table_start = 0
        
        # 找到表头和关键位置
        for pos, line in enumerate(self.lines):
            if "Sample Name" in line:
                self.sample_name = line.split('\t')[1]
            if "<MW_Averages>" in line:
                mw_start = pos
            if "</MW_Averages>" in line:
                mw_end = pos
            if "<Slice_Table>" in line:
                slice_table_start = pos
                break

        # 整理分子量数据
        for line in self.lines[mw_start + 3:mw_end]:
            self.mw_data.append([self.sample_name] + list(line.split('\t'))[1:])
        self.peak_num = len(self.mw_data)
        
        # 提取峰数据
        peak = []
        peak_all = []
        for line in self.lines[slice_table_start + 1:]:
            if ("Peak" in line and len(peak) > 1) or '</Slice_Table>' in line:
                peak_array = np.array(peak[1:], dtype="float")
                self.norm = peak_array[:,2]
                self.mw = peak_array[:,4]
                peak_all.append(peak_array)
                peak = []
                continue
            if "RT" in line:
                continue
            line_parts = line.split('\t')[:-1]
            if line_parts and "-2" in line_parts[0]:
                continue
            peak.append(line_parts)
        self.peak_data = peak_all

    def transform_number(self, num) -> str:
        dig = len(str(num)) - 1
        front = num / (10 ** dig)
        return '{:.1f} × 10$^{}$'.format(front, dig)
    
    def start_width(self):
        return (len(str(self.segmentpos[1])) - 2) * 2
    
    def draw_image(self):
        # 延迟导入 matplotlib,减少启动时间和打包体积
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
        from plottable import Table, ColumnDefinition
        
        plt.cla()
        # 预处理
        # data = np.stack([self.mw, self.norm], axis = 1)
        result_name = self.filename.split('.')[0]
        result = []
        # print(self.segmentpos)
        for id, r in enumerate(self.selectedpos[:-1]):
            result.append(np.sum(self.norm[np.where((self.mw < self.selectedpos[id + 1]) & (self.mw > self.selectedpos[id]))])*100) # 计算区间内总和
        
        if self.draw_table:
            fig = plt.figure(dpi = 300, figsize = (12, 8)) # 画布
        else:
            fig = plt.figure(dpi = 300, figsize = (7.5, 8)) # 无表格画布

        if self.transparent_back:
            fig.patch.set_alpha(0.0)
        # 画图
        gs = gridspec.GridSpec(8,8)
        if not self.draw_table:
            ax = fig.add_subplot(gs[:,:])
        else:   
            ax = fig.add_subplot(gs[:,:5])

        # 计算位置和宽度
        pos_list = [(self.selectedpos[id] * 0.75 + self.selectedpos[id + 1] * 0.25) for id in range(len(self.selectedpos[:-1]))]
        width_list = [i * self.bar_width for i in pos_list]
        
        # 归一化数据
        new_norm = [i * 50 / max(self.norm) for i in self.norm]
        
        # 设置坐标轴粗细
        ax.spines["bottom"].set_linewidth(self.axis_width)
        ax.spines["top"].set_linewidth(self.axis_width)
        ax.spines["left"].set_linewidth(self.axis_width)
        ax.spines["right"].set_linewidth(self.axis_width)
        
        if self.draw_mw:
            ax.plot(self.mw, new_norm, color = self.mw_color, linewidth = self.line_width)
        if self.draw_bar:
            ax.bar(pos_list, result, align = "edge", width = width_list, color = self.bar_color)

        
        plt.xscale("log")
        font1 = {"size": self.axis_font_size, "weight":"bold", "fontname": "Arial"}
        font2 = {"size": self.title_font_size, "weight":"bold", "fontname": "Arial"}
        plt.xlabel("Mw (g /mol)", labelpad = 4, fontdict = font1)
        plt.ylabel("Cumulative%", labelpad = 4, fontdict = font1)

        plt.xticks(weight = 'bold')
        plt.yticks(weight = 'bold')
        plt.title(result_name, pad = 10, fontdict = font2)
        
        if self.draw_table:
            # 表1：分子量区间分布
            ax1 = fig.add_subplot(gs[:6,5:7])
            data1 = []
        
            for id, pos in enumerate(self.selectedpos[1:-1]):
                if id == 0:
                    r1 = "< " + self.transform_number(self.selectedpos[id + 1])
                elif id == len(self.selectedpos[1:-1]) - 1:
                    r1 = ">" + self.transform_number(self.selectedpos[id])
                else:
                    r1 = self.transform_number(self.selectedpos[id]) + " ~ " + self.transform_number(self.selectedpos[id + 1])
                r2 = "{:.2f}%".format(result[id])
                data1.append([r1, r2])
            
        
            data1 = pd.DataFrame(data=data1, columns = ["Mw", "Percent"]).set_index("Mw")
            Table(data1, 
                ax = ax1, 
                textprops = {"fontsize":12,"fontname":'Times New Roman'},
                column_definitions = [ColumnDefinition(name = "Mw", width = 10, textprops = {"ha":"center"}),
                                                        ColumnDefinition(name = "Percent", width = 4, textprops = {"ha":"center"})],
                footer_divider = True,
                row_dividers = True
                )
            
            # 表2：分子量统计数据
            data2 = []
            ax2 = fig.add_subplot(gs[7,5:7])
            for i in self.mw_data:
                data2.append([self.mw_data[0][2], self.mw_data[0][3], self.mw_data[0][7]])
            
            data2 = pd.DataFrame(data = data2,
                                columns = ["Mn", "Mw", "PDI"]).set_index("Mn")
            Table(data2,
                ax = ax2,
                textprops = {"fontsize":12,"fontname":'Times New Roman'},
                column_definitions = [ColumnDefinition(name = "Mw", textprops = {"ha":"center"}),
                                        ColumnDefinition(name = "Mn", textprops = {"ha":"center"}),
                                        ColumnDefinition(name = "PDI", textprops = {"ha":"center"})])

        # plt.tight_layout()
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
        if self.save_picture:
            plt.savefig(os.path.join(self.output_dir, result_name + ".png"), transparent = self.transparent_back)
        if self.display_picture:
            st.pyplot(fig, use_container_width= False)
        plt.close(fig)  # 释放图形资源
        return

    def output_data(self):
        column = ["Samplename", "Mp", "Mn", "Mw", "Mz", "Mz+1", "Mv",  "PD"]

    def read_file_list(self):
        """读取数据目录中的所有.rst文件列表"""
        return [os.path.basename(i) for i in glob.glob(os.path.join(self.data_path, "*.rst"))]

    def run(self):
        """运行分析流程"""
        if len(self.selected_file) == 0:
            # self.file_list = glob.glob(os.path.join(self.data_path, "*.rst"))
            st.warning("没有选中文件")
            return
        
        self.file_list = self.selected_file
        
        for pro, filename in enumerate(self.file_list):
            self.filename = filename
            if self.read_file(filename):
                self.preprocess()
                self.draw_image()   
            
            # 进度条 
            progressBar_mw.progress((pro + 1) / len(self.file_list), "画图进度 {}/{} {:.2f}%".format(pro + 1, len(self.file_list), (pro + 1) * 100/ len(self.file_list)))
        
        return True

class GPCAnalyzer():
    def __init__(self, datadir : str, output_filename : str, save_file : bool = True, save_picture : bool = True, display_mode : bool = True, save_figure_file_gpc = True, test_mode = False):
        # 使用当前脚本所在目录作为根目录，确保配置文件在当前目录下
        self.rootdir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(self.rootdir, "datapath")
        self.output_dir = os.path.join(self.rootdir, "GPC_output")
        self.file_list = None
        self.filename = ""
        # self.heads = {}  # 变量名
        self.lines = []  # raw data 读文件用
        self.output_filename = output_filename
        self.selected_file = None
        
        self.sample_name = ""
        self.mw_data = []  # Mw 数据
        self.peak_num = 0  # 峰数目
        self.peak_pos = [] # 峰 数据位置
        self.peak_data = {}

        # 运行模式
        self.test_mode = test_mode
        self.save_file = save_file
        self.save_picture = save_picture
        self.display_mode = display_mode
        self.save_figure_file_gpc = save_figure_file_gpc

        #画图颜色库
        from cnames import clist
        self.color_list = clist
    
    def reset(self):
        """重置所有数据属性"""
        self.lines = []
        self.filename = ""
        self.sample_name = ""
        self.mw_data = []
        self.peak_num = 0
        self.peak_pos = []
        self.peak_data = {}

    def clear_dir(self):
        if not os.path.exists(self.output_dir):
            return
        for dir in os.listdir(self.output_dir):
            os.remove(os.path.join(self.output_dir, dir))

    def check_dir(self):
        if os.path.exists(os.path.join(self.output_dir, self.output_filename + '.csv')) or os.path.exists(os.path.join(self.output_dir, self.output_filename + '.png')):
            return True
        return False    

    def read_file(self, name):
        self.reset()
        file_path = os.path.join(self.data_path, name)
        with open(file_path, "r", newline="", encoding = "ascii") as file:
            # print(chardet.detect(file.read()))
            for line in file.readlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                self.lines.append(line)
            return True
        return False
        
    def preprocess(self):
        """预处理数据文件，提取分子量和峰数据"""
        mw_start = 0
        mw_end = 0
        slice_table_start = 0
        
        # 找到表头和关键位置
        for pos, line in enumerate(self.lines):
            if "Sample Name" in line:
                self.sample_name = line.split('\t')[1]
            if "<MW_Averages>" in line:
                mw_start = pos
            if "</MW_Averages>" in line:
                mw_end = pos
            if "<Slice_Table>" in line:
                slice_table_start = pos
                break

        # 整理分子量数据
        for line in self.lines[mw_start + 3:mw_end]:
            self.mw_data.append([self.sample_name] + list(line.split('\t'))[1:])
        self.peak_num = len(self.mw_data)
        
        # 提取峰数据
        peak = []
        peak_all = []
        for line in self.lines[slice_table_start + 1:]:
            if ("Peak" in line and len(peak) > 1) or '</Slice_Table>' in line:
                peak_array = np.array(peak[1:], dtype="float")
                peak_all.append(peak_array)
                peak = []
                continue
            if "RT" in line:
                continue
            line_parts = line.split('\t')[:-1]
            if line_parts and "-2" in line_parts[0]:
                continue
            peak.append(line_parts)
        self.peak_data[self.sample_name] = peak_all

    def draw_image(self):
        # 延迟导入 matplotlib,减少启动时间和打包体积
        import matplotlib.pyplot as plt
        
        plt.cla()
        fig = plt.figure(dpi = 300, figsize = (16, 8))
        label = []
        for num, (name, data) in enumerate(self.peak_data.items()):
            for peak in data:
                x = peak[:,5]
                y = peak[:,6]
                plt.plot(x, y, c = self.color_list[num], label = name)
                label.append(name)
        plt.legend(label)
        result_name = self.output_filename
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
        if self.save_picture:
            plt.savefig(os.path.join(self.output_dir, result_name + ".png"))
        if self.display_mode:
            st.pyplot(fig)
        plt.close(fig)  # 释放图形资源
        return

    def output_data(self):
        column = ["Samplename", "Mp", "Mn", "Mw", "Mz", "Mz+1", "Mv",  "PD"]
        result_name = self.output_filename
        data  = pd.DataFrame(data = self.mw_data, columns = column)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
        if self.save_file:
            data.to_csv(os.path.join(self.output_dir, result_name + '.csv'))

    def output_figure_data(self):
        result_name = os.path.join(self.output_dir, self.output_filename + ".xlsx")
        xlsx = pd.ExcelWriter(result_name, engine = "openpyxl")
        for num, (name, data) in enumerate(self.peak_data.items()):
            for peak in data:
                x = peak[:,5]
                y = peak[:,6]
                df = pd.DataFrame(peak[:,5:7])
                df.to_excel(xlsx, sheet_name = name, index = False, header = False)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
        xlsx.close()

    def read_file_list(self):
        return [os.path.basename(i) for i in glob.glob(os.path.join(self.data_path, "*.rst"))]

    def run(self):
        """运行GPC分析流程"""
        if self.selected_file == None:
            self.file_list = [os.path.basename(i) for i in glob.glob(os.path.join(self.data_path, "*.rst"))]
        else:
            self.file_list = self.selected_file

        for pro, filename in enumerate(self.file_list):
            self.filename = filename
            if self.read_file(filename):
                self.preprocess()
            progressBar_gpc.progress((pro + 1) / len(self.file_list), "画图进度 {}/{} {:.2f}%".format(pro + 1, len(self.file_list), (pro + 1) * 100/ len(self.file_list)))
        
        infoBar_gpc.text("绘制图片")
        self.draw_image()
        infoBar_gpc.text("保存数据")
        if self.save_file:
            self.output_data()
        if self.save_figure_file_gpc:
            self.output_figure_data()
        
        return True


# 界面
Mw_ui, gpc_ui, other_ui = st.tabs(["Mw", "GPC", "Other"])
# 使用跨平台的路径分隔符，确保配置文件在当前目录下
default_dir = os.path.join(os.getcwd(), "datapath")

with Mw_ui:
    datapath_mw = st.text_input("数据文件夹", value = default_dir, max_chars = 100, key = "datapath_mw")
    if not os.path.isdir(datapath_mw):
        st.warning("请输入正确路径")

    savePic_mw_col, displayPic_mw_col, *_ = st.columns(spec = 8)
    savePic_mw = savePic_mw_col.checkbox("保存图像", value = True, key = "savePic_mw_col")
    # saveFile_mw = saveFile_mw_col.checkbox("保存文件", value = True, key = "saveFile_mw_col")
    displayPic_mw = displayPic_mw_col.checkbox("显示图片", value = False, key = "displayPic_mw_col")
    
    output_filename_mw_col = st.empty()
    fileSelect_mw_col = st.empty()
                
    mw = MolecularWeightAnalyzer(datapath_mw, save_picture = savePic_mw, display_picture = displayPic_mw, test_mode = False)
    
    # 画图设置
    picSet = st.expander("画图设置")
   
    with picSet:
        barColor_col, MwColor_col, transparentBack_col, drawBar_col, drawMw_col, drawTable_col, settingList_col, deleteSetting_col, *_ = st.columns(spec = 8)
        barWidth_col , lineWidth_col, axisWidth_col, titleFontSize_col, axisFontSize_col, switchSetting_col, settingname_col, saveSetting_col, *_ = st.columns(spec = 8)
        
        mw.bar_color = barColor_col.color_picker("柱状图颜色选择", value = mw.bar_color, key = "barColor_col")
        mw.mw_color = MwColor_col.color_picker("分子量分布颜色选择", value = mw.mw_color, key = "MwColor_col")
        mw.transparent_back = transparentBack_col.checkbox("透明背景", value = mw.transparent_back, key = "transparentBack_col")
        mw.draw_bar = drawBar_col.checkbox("绘制柱状图", value = mw.draw_bar, key = "drawBar_col")
        mw.draw_mw = drawMw_col.checkbox("绘制Mw曲线", value = mw.draw_mw, key = "drawMw_col")
        mw.draw_table = drawTable_col.checkbox("绘制表格", value = mw.draw_table, key = "drawTable_col")
        mw.setting_name = settingList_col.selectbox("设置列表", mw.setting_list(), key = "settingList_col")
        deleteSetting = deleteSetting_col.button("删除设置", key = "deleteSetting_col", on_click = mw.delete_setting, args = [mw.setting_name])
        
        
        mw.bar_width = barWidth_col.slider("柱状图宽度", key = "barWidth_col", min_value = 0.2, max_value = 2.0, step = 0.1, value = mw.bar_width)
        mw.line_width = lineWidth_col.slider("Mw曲线宽度", key = "lineWidth_col", min_value = 0.2, max_value = 2.0, step = 0.1, value = mw.line_width)
        mw.axis_width = axisWidth_col.slider("坐标轴宽度", key = "axisWidth_col", min_value = 0.5, max_value = 2.0, step = 0.1, value = mw.axis_width)
        mw.title_font_size = titleFontSize_col.slider("标题字号", key = "titleFontSize_col", min_value = 14, max_value = 28, step = 1, value = mw.title_font_size)
        mw.axis_font_size = axisFontSize_col.slider("坐标标题字号", key = "axisFontSize_col", min_value = 10, max_value = 18, step = 1, value = mw.axis_font_size)
        switchSetting = switchSetting_col.button("切换设置", key = "switchSetting_col", on_click = mw.change_setting, args = [mw.setting_name])
        newsettingname = settingname_col.text_input("设置名称", key = "saveRegion_col", value = mw.setting_name)
        saveSetting = saveSetting_col.button("保存设置", key = "saveSetting_col", on_click = mw.save_setting, args = [newsettingname], disabled = (mw.setting_name == newsettingname))
        
        
        
    # 区域设置
    rangeSet = st.expander("区域设置")

    with rangeSet:
        selectedRegion = st.multiselect("分割位置", mw.segmentpos, default = mw.selectedpos)
        selectedRegion.sort()
        mw.selectedpos = selectedRegion
        
        new_region_col, addRegion_col, *_ = st.columns(spec = 6)
        new_region = new_region_col.number_input("新分割位置", min_value = 0, max_value = 1000000000)
        addRegion = addRegion_col.button("添加", key = "addRegion_col", on_click = mw.add_region, args = [new_region])
        mw.selected_file = st.multiselect("文件列表", mw.read_file_list(), default = mw.read_file_list())
    # mw.output_filename = st.text_input("输出文件名", value = mw.selectedFile[:-4], max_chars = 100, key = "output_filename_mw", disabled = not (saveFile or savePic))
    run_mw_col, openDir_mw_col, infoBar_mw_col, *_ = st.columns(spec = 8)
    
    
    overlayFile_mw = True
    if mw.check_dir():
        overlayFile_mw = st.checkbox("确认覆盖", key = "overlayFile_mw_col")
        if not overlayFile_mw:
            st.warning("存在相同文件名文件")

    if run_mw_col.button("运行", key = "run_mw_col_mw", disabled = not overlayFile_mw):
        progressBar_mw = st.empty()
        infoBar_mw = infoBar_mw_col.empty()
        result_mw = mw.run()
        infoBar_mw.text("完成！耗时{:.2f}s".format(time.time() - start_time))

    if os.path.isdir(datapath_mw):
        if openDir_mw_col.button("打开目标文件夹", key = "openDir_mw_col_mw"):
            open_folder(mw.output_dir)
    
    progressBar_mw = st.empty()

with gpc_ui:
    datapath_gpc = st.text_input("数据文件夹", value = default_dir, max_chars = 100, key = "datapath_gpc")
    if not os.path.isdir(datapath_gpc):
        st.warning("请输入正确路径")

    save_file_col, save_picture_col, display_mode_col, save_figure_file_gpc_col, selected_gpc_col, draw_mw_col, *_ = st.columns(spec = 8)
    save_file = save_file_col.checkbox("保存样品信息", value = True)
    save_picture = save_picture_col.checkbox("保存图像", value = True)
    display_mode = display_mode_col.checkbox("显示图像", value = True)
    save_figure_file_gpc = save_figure_file_gpc_col.checkbox("保存画图数据", value = False)
    selected = selected_gpc_col.checkbox("选择部分文件")

    # expander = st.expander("", expanded = (saveFile or savePic))

    output_filename = st.text_input("输出文件名", value = time.strftime("%Y%m%d", time.localtime()), max_chars = 100, key = "output_filename", disabled = not (save_file or save_picture))
    overlayFile_col = st.empty()
    fileSelect_col = st.empty()
    run_gpc_col, openDir_gpc_col, infoBar_gpc_col, *_ = st.columns(spec = 8)
    gpc = GPCAnalyzer(datapath_gpc, output_filename, save_file, save_picture, display_mode, save_figure_file_gpc, test_mode = False)

    if selected:
        gpc.selected_file = fileSelect_col.multiselect("文件列表", gpc.read_file_list())
        
    overlayFile = True
    if gpc.check_dir():
        overlayFile = overlayFile_col.checkbox("确认覆盖")
        if not overlayFile:
            st.warning("存在相同文件名文件")  

    if run_gpc_col.button("运行", key = "run_gpc_col", disabled = not overlayFile):
        progressBar_gpc = st.empty()
        infoBar_gpc = infoBar_gpc_col.empty()
        result_gpc = gpc.run()
        infoBar_gpc.text("完成！耗时{:.2f}s".format(time.time() - start_time))

    if os.path.isdir(datapath_gpc):
        if openDir_gpc_col.button("打开目标文件夹", key = "openDir_gpc_col"):
            open_folder(gpc.output_dir)


with other_ui:
    datapath_other = st.text_input("数据文件夹", value = default_dir, max_chars = 100, key = "datapath_other")
    if os.path.isdir(datapath_other):
        clear_confirm = st.checkbox("清理文件夹", value = False)
        # if st.button("清理文件夹", key = "clear_confirm", disabled = not clear_confirm):
        #     dsc = DSC(datapath_other)
        #     dsc.clearDir()
        #     gpc = GPC(datapath_other, output_filename = '')
        #     gpc.clearDir()
        #     st.success("清理完成，耗时{:.2f}s".format(time.time() - start_time))
    else:
        st.warning("请输入正确路径")

with st.sidebar:
    with st.expander("帮助", expanded = True):
        st.markdown('''Tel: 13716441322               
                     Email: liuzhen.bjhy@sinopec.com''')
