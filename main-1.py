import streamlit as st
import re
import os
import time
import chardet
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
from plottable import Table, ColumnDefinition
from scipy import sparse
from scipy.sparse.linalg import spsolve
import warnings
import glob
import pandas as pd
from scipy.signal import find_peaks

# 分隔符统一用，

# os.system("clear")
# os.system("cls")
startTime = time.time()
st.set_page_config(
    page_title='PPR_DATA_PAGE',
    page_icon='D:\\Onedrive\\工作\\Python\\PPR\\PPR\\sinopec.jpg', # todo 
    layout='wide',
    initial_sidebar_state = "collapsed"
)

# DSC功能
class DSC():
    def __init__(self, datadir : str, testMode : bool = False, saveSegMode : bool = True, drawSegMode : bool = True, drawCycle : bool = True, displayPic : bool = True, 
                 saveCyclePic : bool = True, fitMode : bool = True, fitWithModel :  bool = False, leftLength : float = 1.9, rightLength : float = 1.9, prominence : float = 0.15):
        self.rootdir = os.path.abspath(os.path.join(datadir, os.pardir)) + "\\"
        self.datapath = "datapath\\"
        self.cycleDir = "DSC_Cycle\\"
        self.picDir = "DSC_Pic\\"
        self.fileList = None
        self.filename = ""
        self.heads = {}  # 变量名
        self.lines = []  # raw data 读文件用
        self.data = None # raw data
        self.method = {} # 方法
        self.cycle = []  # 循环片段位置
        self.dataSeg = [] # data切片后
        self.region = []

        self.info = " "

        # 运行模式
        self.saveSegMode = saveSegMode
        self.drawSegMode = drawSegMode
        self.drawCycle = drawCycle
        self.displayPic = displayPic
        self.saveCyclePic = saveCyclePic
        self.fitMode = fitMode
        self.fitWithModel = fitWithModel
        self.testMode = testMode

        self.leftLength = leftLength
        self.rightLength = rightLength
        self.prominence = prominence

        #画图颜色库
        from cnames import clist
        self.colorList = clist
    
    def cls(self):
        # os.system("cls")
        # os.system("clear")
        return
    
    def cleardir(self):
        for cycle in glob.glob(self.rootdir + self.cycleDir + 'Cycle*'):
            # print(cycle)
            for file in os.listdir(cycle):
                if os.path.exists(cycle + '/' + file):
                    os.remove(cycle + '/' + file)
            if os.path.exists(cycle):
                os.rmdir(cycle)
            # for num, file in enumerate(glob.glob(cycle + '/*.csv')):
        if not os.path.exists(self.rootdir + self.picDir):
            return
        for dir in os.listdir(self.rootdir + self.picDir):
            # print(dir)
            for file in os.listdir(self.rootdir + self.picDir + dir):
                if os.path.exists(self.rootdir + self.picDir + dir + '/' + file):
                    os.remove(self.rootdir + self.picDir + dir + '/' + file)
            if os.path.exists(self.rootdir +self.picDir + dir):
                os.rmdir(self.rootdir + self.picDir + dir)

    def reset(self):
        # 置空函数
        self.heads = {}  # 变量名
        self.lines = []  # raw data 读文件用
        self.data = None # raw data
        self.method = {} # 方法
        self.cycle = []  # 循环片段位置
        self.dataSeg = [] # data切片后
        self.region = []
        self.peak = []

    def readFile(self, name):
        self.reset()
        lines = []
        # file = self.datapath + '/' + name
        with open(name, "r", newline="", encoding = "UTF-16") as file:
            for line in file.readlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                self.lines.append(line)
            return True
        return False
        
    def preprocess(self):
        table_pos = 0
        peak_pos = 0
        OrgMethod = []
        # 找到表头
        for pos, line in enumerate(self.lines):
            if "Peak" in line:
                peak_pos = pos + 3 
            if "Sig" in line:
                l = line.split()
                title = " ".join(l[1:-1])
                unit = l[-1]
                # self.heads[int(l[0][3:])] = title + '/' + unit  # todo 循环的读数有问题
                self.heads[int(l[0][3:])] = title + '/' + unit  # todo 循环的读数有问题
            if "OrgMethod" in line:
                OrgMethod.append(line.split(":")[1])
            if "StartOfData" in line:
                table_pos = pos
                break
        
        table = []
        # 正则找设定温度和梯度
        re_celsius = re.compile(r"-?[1-9]\d*.\d*|0\.\d*[1-9]\d* °C")
        re_celsiusPerMin = re.compile(r"-?[1-9]\d*.\d*|0\.\d*[1-9]\d* °C/min")
        re_min = re.compile(r"[1-9]\d*.\d*|0\.\d*[1-9]\d* min")
        end = 0
        cycle = [] # 记录序号
        # 分类方法
        for item, m in enumerate(OrgMethod):
            if "Equilibrate" in m:
                start = end
                end = float(re.findall(re_celsius, m)[0])
                grad = 0
                t = 0
                self.cycle.append([item])
            elif "Ramp" in m:
                start = end
                end = float(re.findall(re_celsius, m)[1])
                grad = float(re.findall(re_celsiusPerMin, m)[0])
                if start > end:
                    grad = -grad
                t = (end - start)/grad
                cycle.append(item)
            elif "Isothermal" in m:
                start = end
                t = float(re.findall(re_min, m)[0])
                grad = 0
                # if len(cycle) == 0:
                #     continue
                cycle.append(item)
            elif "Mark" in m:
                cycle.append(item)
                self.cycle.append(cycle) 
                cycle = []
                start = end
                grad = 0
                t = 0
            # 记录方法
            self.method[item] = (start, end, grad, t)
        # print(self.method)
        startTime = float(self.lines[table_pos + 1].split("\t")[0]) + self.method[1][3]
        #整理数据格式
        count_cycle = 3
        for pos, line in enumerate(self.lines[table_pos + 1:]):
            l = line.split("\t")
            # print(l)
            if "-2" in l[0]:
                endTime = float(self.lines[table_pos + 1:][pos - 1].split("\t")[0])
                # startTime, endTime = min(startTime, endTime), max(startTime, endTime) # 开始时间小
                leftSide = startTime + self.leftLength
                rightSide = endTime - self.rightLength - self.method[count_cycle][3]
                self.region.append([leftSide, rightSide])
                startTime = float(self.lines[table_pos + 1:][pos + 1].split("\t")[0])
                count_cycle += 3
                continue
            table.append(line.split("\t"))
        
        endTime = float(self.lines[table_pos + 1:][pos - 1].split("\t")[0])
        startTime, endTime = min(startTime, endTime), max(startTime, endTime) # 开始时间小
        leftSide = startTime + self.leftLength
        rightSide = endTime - self.rightLength
        self.region.append([leftSide, rightSide])
        
        # print("len", len(self.region))
        if peak_pos != 0:   
            for i in range(len(self.region) - 1):
                self.peak.append(list(filter(None, self.lines[peak_pos + i].split(" "))))
        
        self.data = None  # 置空
        self.data = np.array(table, dtype = "float32")

        for region in self.region:
            leftSide, rightSide = region
            self.dataSeg.append(self.data[np.where((self.data[:,0] > leftSide) & (self.data[:,0] < rightSide))])
   
        
    def dataClip(self): # todo del
        leftLength = self.leftLength
        rightLength = self.rightLength
        # print(self.data[:,0])
        # print(np.where((self.data[:,0] < 10) | (self.data[:,0] > 20)))
        startTime = 0
        endTime = 0
        leftSide = 0
        rightSide = 0

        for i, arg in self.method.items():
            if arg[2] == 0 and arg[3] != 0:
                leftSide = startTime + leftLength
                rightSide = endTime - rightLength
                self.region.append([leftSide, rightSide])
                self.dataSeg.append(self.data[np.where((self.data[:,0] > leftSide) & (self.data[:,0] < rightSide))])
            if arg[2] == 0 and arg[3] == 0:
                continue
            startTime = endTime
            endTime += arg[3]
        leftSide = startTime + leftLength
        rightSide = endTime - rightLength
        self.region.append([leftSide, rightSide])
        self.dataSeg.append(self.data[np.where((self.data[:,0] > leftSide) & (self.data[:,0] < rightSide))])
        # for (start,end) in self.region:  # 可以和上面那个合并
        #     self.dataSeg.append(self.data[np.where((self.data[:,0] > start) & (self.data[:,0] < end))])
        # print(self.region)

    def drawImg(self):
        for num, data in enumerate(self.dataSeg):
            plt.cla()
            plt.plot(data[:,1], data[:,2])
            plt.xlabel(self.heads[2])
            plt.ylabel(self.heads[3])
            if not os.path.exists(self.rootdir + self.picDir + self.filename[:-4]):
                os.makedirs(self.rootdir + self.picDir + self.filename[:-4])
            plt.savefig(self.rootdir + self.picDir + self.filename[:-4] + "\\Cycle " + str(num + 1) + ".png")

    def deBaseline(self, x, y, lam=1e9, p=0.05, max_iter=3):
        plt.cla()
        # Check if the peaks are positive or negative
        is_negative = np.mean(y) < 0
        if is_negative:
            y = -y  # Invert the signal if the peaks are negative

        n = len(y)
        # 构造二阶差分矩阵
        D = sparse.diags([1, -2, 1], [0, 1, 2], shape=(n-2, n), format='csc')
        w = np.ones(n)  # 初始权重
        
        for _ in range(max_iter):
            # 构建权重矩阵
            W = sparse.spdiags(w, 0, n, n)
            # 构造方程: (W + lam * D.T @ D) z = W y
            A = W + lam * D.T @ D
            b = W.dot(y)
            z = spsolve(A, b)
            # 更新权重：当y > z时权重为p，否则为1-p
            w = p * (y > z) + (1 - p) * (y <= z)
        
        corrected = y - z
        peaks, _ = find_peaks(corrected, prominence=self.prominence)
        print(x[peaks], [peak[3] for peak in self.peak if len(peak) > 3], "********")
        
        # if is_negative:
        #     corrected = -corrected  # Restore the original sign if the peaks were negative
        #     y = -y
        # plt.plot(x, y, label='原始信号')
        # plt.plot(x, z, label='基线')
        # plt.plot(x, corrected, label='去基线后')
        # plt.plot(x[peaks], corrected[peaks], "x", label='峰值')
        # st.pyplot(plt)
        return corrected
        


    def run(self):
        self.cleardir()
        self.info = "处理原数据..."
        self.fileList = glob.glob(self.rootdir + self.datapath + "*.txt")
        if len(self.fileList) == 0:
            st.warning("数据文件夹中没有相应文件")
            exit()
        # print(self.fileList)
        for pro, file in enumerate(self.fileList): # 找文件列表，todo
            self.filename = file.split('\\')[-1]
            if self.readFile(file):  # 读文件
                infoBar_dsc.text("预处理文件...")
                self.preprocess()   #预处理文件
                infoBar_dsc.text("数据切片...")
                # self.dataClip() # 数据切片，参数为左右缺范围，把恒温段过滤掉
                if self.saveSegMode:
                    infoBar_dsc.text("保存切片数据...")
                    self.saveDataSeg()
                if self.drawSegMode:
                    infoBar_dsc.text("分循环做图...")
                    self.drawImg()
                if self.fitMode:
                    infoBar_dsc.text("拟合做图...")
                    for num, clip in enumerate(self.dataSeg):
                        # print(np.array(clip)[:,2].shape)
                        # print(np.array(clip)[:,2])
                        self.deBaseline(np.array(clip)[:,1], np.array(clip)[:,2])
            self.cls()
            # print("处理原数据...")
            progressBar_dsc.progress((pro + 1) / len(self.fileList), "处理进度 {}/{} {:.2f}%".format(pro + 1, len(self.fileList), (pro + 1) * 100/ len(self.fileList)))

        if self.drawCycle:
            infoBar_dsc.text("绘制各循环叠加图...")
            self.cycleDraw()
        
        return True
    
    def saveDataSeg(self):
        # 按找原本文件名和Cycle 文件夹存数据
        for i in range(len(self.region)):
            if not os.path.exists(self.rootdir + self.cycleDir + "Cycle" + str(i + 1)):
                os.makedirs(self.rootdir + self.cycleDir + "Cycle" + str(i + 1))
            filename = self.rootdir + self.cycleDir + "Cycle" + str(i + 1) + "/" + self.filename[:-4] + ".csv"
            np.savetxt(filename, self.dataSeg[i][:,1:3], delimiter = ',')

    def cycleDraw(self):
        # print(glob.glob(self.rootdir + "/Cycle"+ '//Cycle*'))
        cycleList = glob.glob(self.rootdir + self.cycleDir+ 'Cycle*')
        container = zip(cycleList, cycleList)
        if self.displayPic:
            # 如果显示图片，创建标签页
            tabList = ["Cycle"+ str(i + 1) for i in range(len(cycleList))]
            tabs = st.tabs(tabList)
            container = zip(tabs, cycleList)


        for pro, (tab, cycle) in enumerate(container):
            plt.cla()
            fig = plt.figure(dpi = 300, figsize = (16, 8))
            labels = []
            for num, file in enumerate(glob.glob(cycle + '/*.csv')):
                data = np.loadtxt(file, delimiter = ',')
                name = file.split('\\')[-1][:-4]
                plt.plot(data[:,0], data[:,1], c = self.colorList[num], label = name)
                labels.append(name)

            plt.legend(labels)
            if self.saveCyclePic:
                plt.savefig(cycle + "/result.png")
            self.cls()
            # print("绘制各循环叠加图...")
            progressBar_dsc.progress((pro + 1) / len(cycleList), "画图进度 {}/{} {:.2f}%".format(pro + 1, len(cycleList), (pro + 1) * 100/ len(cycleList)))
        
            if self.displayPic:
                with tab:
                    st.pyplot(fig)

#GPC 功能        
class GPC():
    def __init__(self, datadir : str, output_filename : str, saveFile : bool = True, savePic : bool = True, displayMode : bool = True, saveFigFile_gpc = True, testMode = False):
        self.rootdir = os.path.abspath(os.path.join(datadir, os.pardir)) + "\\"
        self.datapath = "datapath\\"
        self.outputDir = "GPC_output\\"
        self.fileList = None
        self.filename = ""
        # self.heads = {}  # 变量名
        self.lines = []  # raw data 读文件用
        self.output_filename = output_filename
        self.selectedFile = None
        
        self.sampleName = ""
        self.mwData = []  # Mw 数据
        self.peakNum = 0  # 峰数目
        self.peakPos = [] # 峰 数据位置
        self.peakData = {}

        # 运行模式
        self.testMode = testMode
        self.saveFile = saveFile
        self.savePic = savePic
        self.displayMode = displayMode
        self.saveFigFIle_gpc = saveFigFile_gpc

        #画图颜色库
        from cnames import clist
        self.colorList = clist
    
    def reset(self):  # todo
        # 置空函数
        self.heads = {}  # 变量名
        self.lines = []  # raw data 读文件用

    def cleardir(self):
        if not os.path.exists(self.rootdir + self.outputDir):
            return
        for dir in os.listdir(self.rootdir + self.outputDir):
            os.remove(self.rootdir + self.outputDir + dir)

    def checkdir(self):
        if os.path.exists(self.rootdir + self.outputDir + self.output_filename + '.csv') or os.path.exists(self.rootdir + self.outputDir + self.output_filename + '.png'):
            return True
        return False    

    def readFile(self, name):
        self.reset()
        file = self.datapath + '/' + name
        with open(name, "r", newline="", encoding = "ascii") as file:
            # print(chardet.detect(file.read()))
            for line in file.readlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                self.lines.append(line)
            return True
        return False
        
    def preprocess(self):
        mwStart = 0
        mwEnd = 0
        sliceTableStart = 0
        # sliceTableEnde = 0
        # 找到表头
        for pos, line in enumerate(self.lines):
            if "Sample Name" in line:
                l = line.split('\t')
                self.sampleName = line.split('\t')[1]
            if "<MW_Averages>" in line:
                mwStart = pos
            if "</MW_Averages>" in line:
                mwEnd = pos
            if "<Slice_Table>" in line:
                sliceTableStart = pos
                break

        #整理数据格式
        for line in self.lines[mwStart + 3:mwEnd]:
            # print(line)
            # print(self.mwData)
            self.mwData.append([self.sampleName] + list(line.split('\t'))[1:])
        self.peakNum = len(self.mwData)
        
        peak = []
        peakAll = []
        for line in self.lines[sliceTableStart + 1:]:
            if ("Peak" in line and len(peak) > 1) or '</Slice_Table>' in line:
                peak = np.array(peak[1:], dtype = "float")
                peakAll.append(peak)
                peak = []
            if "RT" in line:
                continue
            if "-2" in l[0]:
                continue
            peak.append(line.split('\t')[:-1])  # 最后的Yes 剔除
        self.peakData[self.sampleName] = peakAll

    def drawImg(self):
        plt.cla()
        fig = plt.figure(dpi = 300, figsize = (16, 8))
        label = []
        for num, (name, data) in enumerate(self.peakData.items()):
            for peak in data:
                x = peak[:,5]
                y = peak[:,6]
                plt.plot(x, y, c = self.colorList[num], label = name)
                label.append(name)
        plt.legend(label)
        resultName = self.output_filename
        if not os.path.exists(self.rootdir + "\\" + self.outputDir):
            os.mkdir(self.rootdir + "\\" + self.outputDir)
        if self.savePic:
            plt.savefig(self.rootdir + "\\" + self.outputDir + resultName + ".png")
        if self.displayMode:
            st.pyplot(fig)
        return

    def outPutData(self):
        column = ["Samplename", "Mp", "Mn", "Mw", "Mz", "Mz+1", "Mv",  "PD"]
        resultName = self.output_filename
        data  = pd.DataFrame(data = self.mwData, columns = column)
        if not os.path.exists(self.rootdir + "\\" + self.outputDir):
            os.mkdir(self.rootdir + "\\" + self.outputDir)
        if self.saveFile:
            data.to_csv(self.rootdir + "\\" + self.outputDir + resultName + '.csv')
        # print(self.mwData)

    def outputFigData(self):
        resultName = self.rootdir + "\\" + self.outputDir + self.output_filename + ".xlsx"
        xlsx = pd.ExcelWriter(resultName, engine = "openpyxl")
        for num, (name, data) in enumerate(self.peakData.items()):
            for peak in data:
                x = peak[:,5]
                y = peak[:,6]
                df = pd.DataFrame(peak[:,5:7])
                df.to_excel(xlsx, sheet_name = name, index = False, header = False)

        if not os.path.exists(self.rootdir + "\\" + self.outputDir):
            os.mkdir(self.rootdir + "\\" + self.outputDir)
        xlsx.close()

    def readFileList(self):
        return [i.split("\\")[-1] for i in glob.glob(self.rootdir + "\\" + self.datapath + "\\*.rst")]

    def run(self):
        # print(glob.glob(self.datapath + "/*.rst"))
        if self.selectedFile == None:
            self.fileList = glob.glob(self.rootdir + "\\" + self.datapath + "\\*.rst")
        else:
            self.fileList = [self.rootdir + "\\" + self.datapath + "\\" + name for name in self.selectedFile]

        for pro, file in enumerate(self.fileList):
            self.filename = file.split('\\')[-1]
            if self.readFile(file):
                self.preprocess()
            progressBar_gpc.progress((pro + 1) / len(self.fileList), "画图进度 {}/{} {:.2f}%".format(pro + 1, len(self.fileList), (pro + 1) * 100/ len(self.fileList)))
        
        infoBar_gpc.text("绘制图片")
        self.drawImg()
        infoBar_gpc.text("保存数据")
        if self.saveFile:
            self.outPutData()
        if self.saveFigFIle_gpc:
            self.outputFigData()
        
        return True

class Mw():
    def __init__(self, datadir : str, output_filename : str, segmentpos : list = [], saveFile : bool = True, savePic : bool = True, displayPic : bool = False, testMode = False):
        self.rootdir = os.path.abspath(os.path.join(datadir, os.pardir)) + "\\"
        self.datapath = "datapath\\"
        self.outputDir = "Mw_output\\"
        self.fileList = None
        self.filename = ""
        # self.heads = {}  # 变量名
        self.lines = []  # raw data 读文件用
        self.output_filename = output_filename
        self.selectedFile = None
        
        self.sampleName = ""
        self.mwData = []  # Mw 数据
        self.peakNum = 0  # 峰数目
        self.peakPos = [] # 峰 数据位置
        self.peakData = {}
        self.segmentpos = segmentpos
        self.segmentnum = len(self.segmentpos)
        
        self.norm = None
        self.mw = None
        

        # 运行模式
        self.testMode = testMode
        self.saveFile = saveFile
        self.savePic = savePic
        self.displayPic = displayPic
        
        #画图颜色库
        from cnames import clist
        self.colorList = clist
    
    def reset(self):  # todo
        # 置空函数
        self.heads = {}  # 变量名
        self.lines = []  # raw data 读文件用
        self.mwData = []

    def cleardir(self):
        if not os.path.exists(self.rootdir + self.outputDir):
            return
        for dir in os.listdir(self.rootdir + self.outputDir):
            os.remove(self.rootdir + self.outputDir + dir)

    def checkdir(self) -> bool:
        for file in self.selectedFile:
            # print(self.rootdir + self.outputDir + file.split('.')[0] + '.png')
            if os.path.exists(self.rootdir + self.outputDir + file.split('.')[0] + '.png'):
                return True
        return False    

    def readFile(self, name):
        self.reset()
        file = self.datapath + '/' + name
        with open(name, "r", newline="", encoding = "ascii") as file:
            # print(chardet.detect(file.read()))
            for line in file.readlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                self.lines.append(line)
            return True
        return False
        
    def preprocess(self):
        mwStart = 0
        mwEnd = 0
        sliceTableStart = 0
        # sliceTableEnde = 0
        # 找到表头.
        for pos, line in enumerate(self.lines):
            if "Sample Name" in line:
                l = line.split('\t')
                self.sampleName = line.split('\t')[1]
            if "<MW_Averages>" in line:
                mwStart = pos
            if "</MW_Averages>" in line:
                mwEnd = pos
            if "<Slice_Table>" in line:
                sliceTableStart = pos
                break

        #整理数据格式
        for line in self.lines[mwStart + 3:mwEnd]:
            # print(line)
            # print(self.mwData)
            self.mwData.append([self.sampleName] + list(line.split('\t'))[1:])
        self.peakNum = len(self.mwData)
        
        peak = []
        peakAll = []
        for line in self.lines[sliceTableStart + 1:]:
            if ("Peak" in line and len(peak) > 1) or '</Slice_Table>' in line:
                peak = np.array(peak[1:], dtype = "float")
                self.norm = peak[:,2]
                self.mw = peak[:,4]
                peakAll.append(peak)
                peak = []
            if "RT" in line:
                continue
            if "-2" in l[0]:
                continue
            peak.append(line.split('\t')[:-1])  # 最后的Yes 剔除
        self.peakData = peakAll

    def trannum(self, num) -> str:
        dig = len(str(num)) - 1
        front = num / (10 ** dig)
        
        return '{:.1f} × 10$^{}$'.format(front, dig)
    
    def startWidth(self):
        return (len(str(self.segmentpos[1])) - 2) * 2
    
    def drawImg(self):
        plt.cla()
        # 预处理
        # data = np.stack([self.mw, self.norm], axis = 1)
        resultName = self.filename.split('.')[0]
        result = []
        # print(self.segmentpos)
        for id, r in enumerate(self.segmentpos[:-1]):
            result.append(np.sum(self.norm[np.where((self.mw < self.segmentpos[id + 1]) & (self.mw > self.segmentpos[id]))])*100) # 计算区间内综合
    
        fig = plt.figure(dpi = 300, figsize = (12, 8)) # 画布
        # 画图
        gs = gridspec.GridSpec(8,8)

        ax = fig.add_subplot(gs[:,:5])
        # namelist = [self.trannum(i) for i in self.segmentpos[:-1]]
        poslist = self.segmentpos[:-1]
        poslist = [(self.segmentpos[id] * 0.75 + self.segmentpos[id + 1] * 0.25) for id, v in enumerate(self.segmentpos[:-1])]
        # widthlist = [25*10**(i/2) for i in range(self.startWidth(), len(self.segmentpos[:-1]) + self.startWidth(), 1)]
        widthlist = [i * 1.2 for i in poslist]
        # print(poslist, widthlist)
        
        newnorm = [i * 50 / max(self.norm) for i in self.norm] # 归一化
        
        ax.plot(self.mw, newnorm)
        ax.bar(poslist, result, color = "blue", align = "edge", width = widthlist)
        
        plt.xscale("log")
        font1 = {"size": 14, "weight":"bold", "fontname": "Arial"}
        font2 = {"size": 20, "weight":"bold", "fontname": "Arial"}
        plt.xlabel("Mw", labelpad = 4, fontdict = font1)
        plt.ylabel("Cumulative%", labelpad = 4, fontdict = font1)

        plt.xticks(weight = 'bold')
        plt.yticks(weight = 'bold')
        plt.title(resultName, pad = 10, fontdict = font2)
        
        # 表1
        ax1 = fig.add_subplot(gs[:6,5:7])
        data1 = []
       
        for id, pos in enumerate(self.segmentpos[1:-1]):
            # print(result[id], self.segmentpos[id + 1])
            if id == 0:
                r1 = "< " + self.trannum(self.segmentpos[id + 1])
            elif id == len(self.segmentpos[1:-1]) - 1:
                r1 = ">" + self.trannum(self.segmentpos[id])
            else:
                r1 = self.trannum(self.segmentpos[id]) + " ~ " + self.trannum(self.segmentpos[id + 1])
            r2 = "{:.2f}%".format(result[id])
            data1.append([r1, r2])
            pass
        
        data1 = pd.DataFrame(data=data1, columns = ["Mw", "Percent"]).set_index("Mw")
        Table(data1, 
              ax = ax1, 
              textprops = {"fontsize":12,"fontname":'Times New Roman'},
              column_definitions = [ColumnDefinition(name = "Mw", width = 10, textprops = {"ha":"center"}),
                                                     ColumnDefinition(name = "Percent", width = 4, textprops = {"ha":"center"})],
              footer_divider = True,
              row_dividers = True
              )
        
        # 表2
        data2 = []
        ax2 = fig.add_subplot(gs[7,5:7])
        for i in self.mwData:
            data2.append([self.mwData[0][2], self.mwData[0][3], self.mwData[0][7]])
        
        data2 = pd.DataFrame(data = data2,
                             columns = ["Mn", "Mw", "PDI"]).set_index("Mn")
        Table(data2,
              ax = ax2,
              textprops = {"fontsize":12,"fontname":'Times New Roman'},
              column_definitions = [ColumnDefinition(name = "Mw", textprops = {"ha":"center"}),
                                    ColumnDefinition(name = "Mn", textprops = {"ha":"center"}),
                                    ColumnDefinition(name = "PDI", textprops = {"ha":"center"})])

        # plt.tight_layout()
        
        if not os.path.exists(self.rootdir + "\\" + self.outputDir):
            os.mkdir(self.rootdir + "\\" + self.outputDir)
        if self.savePic:
            plt.savefig(self.rootdir + "\\" + self.outputDir + resultName + ".png")
        if self.displayPic:
            st.pyplot(fig, use_container_width= False)
        return

    def outPutData(self):
        column = ["Samplename", "Mp", "Mn", "Mw", "Mz", "Mz+1", "Mv",  "PD"]
        # resultName = self.output_filename
        # data  = pd.DataFrame(data = self.mwData, columns = column)
        # if not os.path.exists(self.rootdir + "\\" + self.outputDir):
        #     os.mkdir(self.rootdir + "\\" + self.outputDir)
        # if self.saveFile:
        #     data.to_csv(self.rootdir + "\\" + self.outputDir + resultName + '.csv')
        # # print(self.mwData)


    def outputFigData(self):
        resultName = self.rootdir + "\\" + self.outputDir + self.output_filename + ".xlsx"
        xlsx = pd.ExcelWriter(resultName, engine = "openpyxl")
        for num, (name, data) in enumerate(self.peakData.items()):
            for peak in data:
                x = peak[:,5]
                y = peak[:,6]
                df = pd.DataFrame(peak[:,5:7])
                df.to_excel(xlsx, sheet_name = name, index = False, header = False)

        if not os.path.exists(self.rootdir + "\\" + self.outputDir):
            os.mkdir(self.rootdir + "\\" + self.outputDir)
        xlsx.close()

    def readFileList(self):
        return [i.split("\\")[-1] for i in glob.glob(self.rootdir + "\\" + self.datapath + "\\*.rst")]

    def run(self):
        # print(glob.glob(self.datapath + "/*.rst"))
        if len(self.selectedFile) == 0:
            # self.fileList = glob.glob(self.rootdir + "\\" + self.datapath + "\\*.rst")
            st.warning("没有选中文件")
            return
        else:
            self.fileList = [self.rootdir + "\\" + self.datapath + "\\" + name for name in self.selectedFile]
            
        for pro, file in enumerate(self.fileList):
            self.filename = file.split('\\')[-1]
            if self.readFile(file):
                self.preprocess()
                self.drawImg()   
            
            # 进度条 
            progressBar_mw.progress((pro + 1) / len(self.fileList), "画图进度 {}/{} {:.2f}%".format(pro + 1, len(self.fileList), (pro + 1) * 100/ len(self.fileList)))
        
        return True

# 界面
dsc_ui, gpc_ui, Mw_ui, other_ui = st.tabs(["DSC", "GPC", "Mw", "Other"])
default_dir = 'C:\\Users\\Lenovo\\Desktop\\python\\streamlit\\datapath\\'
# default_dir = 'D:\Onedrive\工作\PPR\PPR\datapath'

with dsc_ui:
    ## 默认渲染到主界面 
    datapath_dsc = st.text_input("数据文件夹", value = default_dir, placeholder = "数据路径", key = "datapath_dsc")
    if not os.path.isdir(datapath_dsc):
        st.warning("请输入正确路径")
    # 参数选择
    saveSegMode_col, drawSegMode_col, drawCycle_col, displayPic_col, saveCyclePic_col, fitMode_col, fitWithModel_col, testMode_col = st.columns(spec = 8)
    saveSegMode = saveSegMode_col.checkbox("保存各片段数据", value = True)
    drawSegMode = drawSegMode_col.checkbox("绘制各片段数据", value = True)
    drawCycle = drawCycle_col.checkbox("绘制各循环", value = saveSegMode, disabled = not saveSegMode)
    displayPic = displayPic_col.checkbox("显示各循环", value = saveSegMode and drawCycle, disabled = not (saveSegMode and drawCycle))
    saveCyclePic = saveCyclePic_col.checkbox("保存各循环", value = saveSegMode and drawCycle, disabled = not (saveSegMode and drawCycle))
    fitMode = fitMode_col.checkbox("拟合各片段数据", value = False)
    fitWithModel = fitWithModel_col.checkbox("拟合各片段数据（机器学习）", value = False, disabled = True)
    testMode = testMode_col.checkbox("测试模式", value = False, disabled = True)

    leftSide_col, prominence_col, rightSide_col = st.columns(spec = 3)
    leftSide = leftSide_col.slider(label = "左边界/min", min_value = 0.0, max_value = 3.0, value = 0.5, step = 0.1)
    if fitMode:
        prominence = prominence_col.slider(label = "峰突出程度", min_value = 0.01, max_value = 1.00, value = 0.15, step = 0.01)
    else:
        prominence = 0
    rightSide = rightSide_col.slider(label = "右边界/min", min_value = 0.0, max_value = 3.0, value = 0.5, step = 0.1)
    
    run_col_dsc,  infoBar_col_dsc, openDir_dsc_col,*_ = st.columns(spec = 11)

    avilible = any([saveSegMode, drawSegMode, drawCycle, saveCyclePic, displayPic, fitMode, fitWithModel])

    if not avilible:
        st.warning("至少选择一个项目")

    dsc = DSC(datadir = datapath_dsc, testMode = testMode, saveSegMode = saveSegMode, drawSegMode = drawSegMode, drawCycle = drawCycle, displayPic = displayPic, 
                    saveCyclePic = saveCyclePic, fitMode = fitMode, fitWithModel = fitWithModel, leftLength = leftSide, rightLength = rightSide, prominence = prominence)
    if run_col_dsc.button("运行", key = "run_col_dsc", disabled = not avilible):
        progressBar_dsc = st.empty()
        infoBar_dsc = infoBar_col_dsc.empty()
        result_dsc = dsc.run()
        infoBar_dsc.text("完成！耗时{:.2f}s".format(time.time() - startTime))

    if os.path.isdir(datapath_dsc):
        if openDir_dsc_col.button("打开目标文件夹", key = "openDir_dsc_col"):
            os.system("explorer.exe {}".format(dsc.rootdir))

with gpc_ui:
    datapath_gpc = st.text_input("数据文件夹", value = default_dir, max_chars = 100, key = "datapath_gpc")
    if not os.path.isdir(datapath_gpc):
        st.warning("请输入正确路径")

    saveFile_col, savePic_col, displayMode_col, saveFigFile_gpc_col, selected_gpc_col, draw_mw_col, *_ = st.columns(spec = 8)
    saveFile = saveFile_col.checkbox("保存文件", value = True)
    savePic = savePic_col.checkbox("保存图像", value = True)
    displayMode = displayMode_col.checkbox("显示图像", value = True)
    saveFigFile_gpc = saveFigFile_gpc_col.checkbox("保存画图数据", value = True)
    selected = selected_gpc_col.checkbox("选择部分文件")

    # expander = st.expander("", expanded = (saveFile or savePic))

    output_filename = st.text_input("输出文件名", value = time.strftime("%Y%m%d", time.localtime()), max_chars = 100, key = "output_filename", disabled = not (saveFile or savePic))
    overlayFile_col = st.empty()
    fileSelect_col = st.empty()
    run_gpc_col, openDir_gpc_col, infoBar_gpc_col, *_ = st.columns(spec = 8)
    gpc = GPC(datapath_gpc, output_filename, saveFile, savePic, displayMode, saveFigFile_gpc, testMode = False)

    if selected:
        gpc.selectedFile = fileSelect_col.multiselect("文件列表", gpc.readFileList())
        
    overlayFile = True
    if gpc.checkdir():
        overlayFile = overlayFile_col.checkbox("确认覆盖")
        if not overlayFile:
            st.warning("存在相同文件名文件")  

    if run_gpc_col.button("运行", key = "run_gpc_col", disabled = not overlayFile):
        progressBar_gpc = st.empty()
        infoBar_gpc = infoBar_gpc_col.empty()
        result_gpc = gpc.run()
        infoBar_gpc.text("完成！耗时{:.2f}s".format(time.time() - startTime))

    if os.path.isdir(datapath_gpc):
        if openDir_gpc_col.button("打开目标文件夹", key = "openDir_gpc_col"):
            os.system("explorer.exe {}".format(gpc.rootdir + gpc.outputDir))

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
    
    rangeset = st.expander("区域设置")
    segmentpos = []
    with rangeset:
        region = [0, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000, 10000000, 50000000] # todo
        rangenum = st.slider("区域数目", min_value = 1, max_value = 15, value = 10, step = 1, key = "rangenum")
        for i in range(rangenum):
            result = st.select_slider("区域{}".format(i + 1), region, value = region[i])
            segmentpos.append(result)
            
    mw = Mw(datapath_mw, "", segmentpos = segmentpos, savePic = savePic_mw, displayPic = displayPic_mw, testMode = False)
    mw.selectedFile = st.multiselect("文件列表", mw.readFileList(), default = mw.readFileList())
    # mw.output_filename = st.text_input("输出文件名", value = mw.selectedFile[:-4], max_chars = 100, key = "output_filename_mw", disabled = not (saveFile or savePic))
    run_mw_col, openDir_mw_col, infoBar_mw_col, *_ = st.columns(spec = 8)
    
    
    overlayFile_mw = True
    if mw.checkdir():
        overlayFile_mw = st.checkbox("确认覆盖", key = "overlayFile_mw_col")
        if not overlayFile_mw:
            st.warning("存在相同文件名文件")

    if run_mw_col.button("运行", key = "run_mw_col_mw", disabled = not overlayFile_mw):
        progressBar_mw = st.empty()
        infoBar_mw = infoBar_mw_col.empty()
        result_mw = mw.run()
        infoBar_mw.text("完成！耗时{:.2f}s".format(time.time() - startTime))

    if os.path.isdir(datapath_mw):
        if openDir_mw_col.button("打开目标文件夹", key = "openDir_mw_col_mw"):
            os.system("explorer.exe {}".format(mw.rootdir + mw.outputDir))
    
    progressBar_mw = st.empty()

with other_ui:
    datapath_other = st.text_input("数据文件夹", value = default_dir, max_chars = 100, key = "datapath_other")
    if os.path.isdir(datapath_other):
        clear_confirm = st.checkbox("清理文件夹", value = False)
        if st.button("清理文件夹", key = "clear_confirm", disabled = not clear_confirm):
            dsc = DSC(datapath_other)
            dsc.cleardir()
            gpc = GPC(datapath_other, output_filename = '')
            gpc.cleardir()
            st.success("清理完成，耗时{:.2f}s".format(time.time() - startTime))
    else:
        st.warning("请输入正确路径")

with st.sidebar:
    with st.expander("帮助", expanded = True):
        st.markdown('''Tel: 13716441322               
                     Email: liuzhen.bjhy@sinopec.com''')
