# PolyAnalyzer - 高分子材料数据可视化工具

[English](README_EN.md) | 中文

一个专业的高分子材料数据分析与可视化工具，集成了GPC（凝胶渗透色谱）和DSC（差示扫描量热法）分析功能，为科研人员提供高效、直观的数据处理体验。

## ✨ 核心功能

### 📊 GPC 凝胶渗透色谱分析
- 自动读取和处理GPC数据文件
- 生成精美的柱状图和分子量分布曲线
- 创建专业的分子量数据表格
- 批量处理多个样品数据

### 🔥 DSC 差示扫描量热法分析
- 自动识别并解析DSC热流数据
- 智能提取多循环测试数据
- 绘制热流-温度曲线
- 支持峰位自动识别和居中显示
- 多循环数据对比分析
- 数据分段保存和可视化

### 🎨 通用特性
- 支持自定义颜色、线宽、字体大小等样式
- 批量导出高质量图片（PNG，300 DPI）
- 基于Streamlit的现代化Web界面
- 多语言界面支持（中文/English）
- 灵活的配置管理系统
- 完整的日志记录功能
- 多种打包方式，满足不同部署需求

## 🚀 快速开始

### 方式一：Windows 便携版（推荐 - 零门槛使用）

**适用对象：科研人员、实验室用户、无编程经验者**

#### 使用步骤：
1. 从 [Releases](https://github.com/FrankLaurance/PolyAnalyzer/releases) 下载最新的 `PolyAnalyzer_Windows_Portable_vX.X.X.zip`
2. 解压到任意位置（建议路径不含中文和空格）
3. 双击 `启动应用.bat` 或 `Start_App.bat`
4. 浏览器自动打开应用界面，即可开始使用

#### 特点：
- ✅ 完全绿色免安装，无需配置Python环境
- ✅ 内置所有依赖，体积约 150-200MB
- ✅ 支持完整的本地文件读写功能
- ✅ 卸载只需删除文件夹
- ✅ 支持离线使用，数据安全有保障

### 方式二：从源码运行（开发者与技术用户）

**适用对象：开发者、需要定制功能、跨平台使用**

#### 系统要求：
- Python 3.8 或更高版本
- pip 包管理器

#### 安装步骤：

```bash
# 1. 克隆项目仓库
git clone https://github.com/FrankLaurance/PolyAnalyzer.git
cd PolyAnalyzer

# 2. 创建虚拟环境（强烈推荐）
python -m venv myenv

# 3. 激活虚拟环境
# macOS/Linux:
source myenv/bin/activate
# Windows:
myenv\Scripts\activate

# 4. 安装依赖包
pip install -r requirements.txt
```

#### 运行程序：

```bash
# 方式1：使用 Streamlit 直接运行
streamlit run main.py

# 方式2：使用项目提供的运行脚本
python run_main.py
```

程序将自动在浏览器中打开，默认地址为 `http://localhost:8501`

### 方式三：PyInstaller 单文件版本（需自行编译）

**适用对象：需要单文件分发、简化部署的场景**

#### 编译步骤：

**前置要求：**
```bash
# 确保已安装项目依赖
pip install -r requirements.txt
```

**自动编译（推荐）：**
```bash
# macOS/Linux
chmod +x build.sh
./build.sh

# Windows
.\build.ps1
```

**手动编译：**
```bash
pip install pyinstaller
pyinstaller PolyAnalyzer.spec
```

生成的 `PolyAnalyzer.exe` 位于 `dist/PolyAnalyzer/` 目录

> 💡 **说明：** build脚本会自动安装PyInstaller，但不会安装项目依赖，请确保先执行 `pip install -r requirements.txt`

#### 使用说明：
1. 将生成的 exe 文件分发给用户
2. 用户双击即可运行，无需安装

#### 注意事项：
- ⚠️ 文件体积较大（约 300-500MB），因包含完整运行环境
- ⚠️ 首次启动需要解压缓存，启动时间约 10-30 秒
- ⚠️ 部分杀毒软件可能误报，可添加信任或使用便携版
- ℹ️ 详细打包说明请参阅 [BUILD_README.md](BUILD_README.md)

### 📦 部署方式对比

| 方式 | 体积 | 启动速度 | 用户体验 | 推荐人群 | 跨平台 |
|------|------|---------|----------|----------|--------|
| **Windows 便携版** | ~150MB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 实验室用户、科研人员 | Windows |
| **源码运行** | ~10MB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 开发者、技术用户 | 全平台 |
| **PyInstaller exe** | ~300-500MB | ⭐⭐⭐ | ⭐⭐⭐ | 需要单文件分发 | Windows |

## 📖 使用说明

### 0. 语言切换

应用支持**中文（简体）**和**English**双语界面：
1. 启动应用后，在左侧边栏顶部找到 **"语言/Language"** 下拉菜单
2. 选择您偏好的语言
3. 界面将自动刷新并切换至所选语言

详细的国际化说明请参阅：[I18N_README.md](I18N_README.md)

### 1. 准备数据文件

#### GPC 数据文件要求：
- 支持的格式：`.txt`、`.csv` 等文本文件
- 必需的数据列：
  - 分子量数据：Mn（数均分子量）、Mw（重均分子量）、Mz（Z均分子量）
  - 分布指数：PDI（多分散性指数）
  - 分子量分布曲线数据

#### DSC 数据文件要求：
- 支持的格式：TA仪器导出的 `.txt` 或 `.rst` 文件
- 文件应包含：
  - 热流（Heat Flow）数据
  - 温度（Temperature）数据
  - 时间（Time）数据
  - 方法（Method）信息（用于自动识别循环）

### 2. 配置参数

应用提供了丰富的配置选项，在Web界面的侧边栏中可进行设置：

#### GPC 分析配置：

**基本设置：**
- 📁 数据目录路径
- 💾 CSV文件保存选项
- 🖼️ 图片生成与保存选项

**样式设置：**
- 🎨 柱状图颜色（默认：#002FA7）
- 🎨 分子量曲线颜色（默认：#FF6A07）
- 📏 柱状图宽度
- 📏 曲线线宽
- 📏 坐标轴粗细

**字体设置：**
- 📝 标题字体大小
- 📝 坐标轴字体大小

**图表选项：**
- ☑️ 绘制柱状图
- ☑️ 绘制分子量曲线
- ☑️ 生成数据表格
- ☑️ 使用透明背景

#### DSC 分析配置：

**基本设置：**
- 📁 DSC数据目录路径
- 💾 分段数据保存选项
- 🖼️ 循环对比图保存选项

**分析参数：**
- 📊 左右边界范围（用于峰位显示范围）
- 🔍 峰检测参数

**绘图选项：**
- ☑️ 保存分段数据（CSV格式）
- ☑️ 绘制分段图
- ☑️ 绘制循环对比图
- ☑️ 峰位自动居中显示

**样式设置：**
- 🎨 曲线颜色
- 📏 线宽
- 📏 坐标轴粗细
- 📝 字体大小设置

### 3. 运行分析

#### GPC 分析流程：
1. 在侧边栏中选择或输入数据目录路径
2. 根据需要调整各项参数和样式设置
3. 点击 **"开始处理"** 或 **"Run"** 按钮
4. 程序将自动处理目录中的所有数据文件
5. 处理进度会实时显示在界面上
6. 完成后会显示处理时间和结果预览

#### DSC 分析流程：
1. 切换到 **"DSC分析"** 标签页
2. 选择DSC数据目录
3. 配置分析参数（循环数、峰检测参数等）
4. 点击 **"运行"** 按钮开始分析
5. 程序会自动：
   - 识别多循环数据
   - 提取各循环的热流-温度数据
   - 保存分段数据为CSV文件
   - 生成各循环的独立曲线图
   - 生成循环对比叠加图

### 4. 查看与导出结果

#### 输出文件位置：
- **GPC结果：** 
  - 图片：`datapath/样品名称/` 文件夹
  - CSV数据：`GPC_output/` 文件夹
  - 分子量汇总：`Mw_output/` 文件夹

- **DSC结果：**
  - 循环数据：`DSC_Cycle/CycleX/` 文件夹（CSV格式）
  - 曲线图：`DSC_Pic/样品名称/` 文件夹（PNG格式）
  - 循环对比图：各Cycle文件夹下的 `result.png`

#### 便捷操作：
- 点击 **"打开输出文件夹"** 按钮可直接访问结果目录
- 所有生成的图片都会在界面中实时预览
- 支持在浏览器中直接查看和下载图片

## 🔧 配置文件说明

### GPC 配置文件

程序使用 `setting/defaultSetting.ini` 作为GPC分析的默认配置文件：

```ini
[DEFAULT]
# 基本设置
DataDir = datapath                # 数据目录
SaveFile = True                   # 是否保存CSV文件
SavePicture = True                # 是否保存图片
DisplayPicture = False            # 是否在界面显示图片

# 图形样式
BarColor = #002FA7                # 柱状图颜色（深蓝色）
MwColor = #FF6A07                 # 分子量曲线颜色（橙色）
BarWidth = 1.2                    # 柱状图宽度
LineWidth = 1.0                   # 曲线线宽
AxisWidth = 1.0                   # 坐标轴粗细

# 字体设置
TitleFontSize = 20                # 标题字体大小
AxisFontSize = 14                 # 坐标轴字体大小

# 图表选项
DrawBar = True                    # 绘制柱状图
DrawMw = True                     # 绘制分子量曲线
DrawTable = True                  # 生成数据表格
TransparentBack = True            # 使用透明背景
```

### DSC 配置文件

程序使用 `setting/defaultDSCSetting.ini` 作为DSC分析的默认配置文件：

```ini
[DEFAULT]
# 曲线样式
curve_color = #002FA7             # 曲线颜色
line_width = 1.0                  # 线宽
axis_width = 1.0                  # 坐标轴粗细

# 字体设置
title_font_size = 20              # 标题字体大小
axis_font_size = 14               # 坐标轴字体大小

# 图形选项
transparent_back = True           # 使用透明背景
```

### 配置管理

- ✏️ 可直接编辑INI文件修改默认配置
- 💾 在Web界面中修改参数后可保存为新的配置方案
- 📋 支持多配置方案管理，可随时切换
- 🔄 支持删除自定义配置，恢复默认设置

## 📦 打包说明

### 方法一：打包 Windows 便携版（推荐）

**特点：体积小、绿色便携、用户体验最佳**

```bash
# 在 macOS/Linux 上执行
bash package_windows.sh
```

脚本会自动：
1. 下载 Python 嵌入式版本
2. 安装所有依赖
3. 创建启动脚本
4. 打包成 ZIP 文件

生成的文件结构：
```
PolyAnalyzer_Windows_Portable_v1.0/
├── 启动应用.bat          # 用户双击启动
├── python/               # 内嵌 Python 环境
├── main.py              # 应用代码
├── datapath/            # 数据目录
└── 使用说明.txt          # 用户文档
```

**优势：**
- ✅ 体积约 150-200MB（比 PyInstaller 小 50%）
- ✅ 完全绿色便携，无需安装
- ✅ 支持读写本地文件
- ✅ 用户体验好，双击即用

### 方法二：PyInstaller 打包

**特点：单文件 exe，但体积较大**

**自动打包脚本：**

```bash
# macOS/Linux
chmod +x build.sh
./build.sh

# Windows
.\build.ps1
```

**手动打包：**

```bash
pip install pyinstaller
pyinstaller PolyAnalyzer.spec
```

生成的 exe 文件位于 `dist/PolyAnalyzer` 目录。

**注意事项：**
- 文件较大（300-500MB）
- 可能需要 UPX 压缩
- 详细说明见 [BUILD_README.md](BUILD_README.md)

### 打包方式选择建议

| 场景 | 推荐方式 | 原因 |
|------|----------|------|
| 分发给普通用户 | **Windows 便携版** | 体积小、用户体验好 |
| 需要单文件 | PyInstaller | 便于分发和管理 |
| 开发测试 | 源码运行 | 灵活方便 |

## 📋 主要依赖包

### 核心依赖
- **streamlit** >= 1.20.0 - Web界面框架
- **numpy** >= 1.20.0 - 数值计算
- **pandas** >= 1.3.0 - 数据处理
- **matplotlib** >= 3.5.0 - 图形绘制

### 功能依赖
- **plottable** >= 0.1.0 - 表格绘制
- **scipy** >= 1.7.0 - 科学计算（DSC峰检测）
- **chardet** >= 4.0.0 - 文件编码检测

完整依赖列表请查看 [requirements.txt](requirements.txt)

## 🖥️ 系统要求

### 源码运行
- **Python版本：** 3.8 或更高
- **操作系统：** Windows / macOS / Linux
- **内存：** 至少 2GB RAM
- **磁盘空间：** 至少 500MB（包含数据文件）

### Windows 便携版
- **操作系统：** Windows 7 或更高
- **内存：** 至少 2GB RAM
- **磁盘空间：** 至少 500MB（包含程序和数据）

## 📝 项目结构

```
PolyAnalyzer/
├── main.py                    # 主程序文件（包含GPC/DSC/Mw分析器）
├── ui.py                      # Streamlit Web界面
├── i18n.py                    # 国际化模块（多语言支持）
├── run_main.py               # 运行启动脚本
├── cnames.py                 # 颜色名称映射
├── requirements.txt          # Python依赖包列表
├── PolyAnalyzer.spec            # PyInstaller打包配置文件
├── package_windows.sh        # Windows便携版打包脚本
├── build.sh / build.ps1     # PyInstaller打包脚本
├── BUILD_README.md          # 打包详细说明文档
├── I18N_README.md           # 国际化说明文档
├── OPTIMIZATION_REPORT.md   # 优化报告
├── README.md / README_EN.md # 项目说明文档
├── setting/                  # 配置文件目录
│   ├── defaultSetting.ini   # GPC默认配置
│   ├── defaultDSCSetting.ini # DSC默认配置
│   └── language.json        # 语言偏好（自动生成）
├── datapath/                 # GPC数据文件目录（输入）
├── GPC_output/              # GPC分析结果输出
├── Mw_output/               # 分子量汇总输出
├── DSC_Cycle/               # DSC循环数据输出
├── DSC_Pic/                 # DSC图形输出
└── logs/                     # 日志文件目录
```

## 🐛 故障排除

### 问题1：程序无法启动
- 确认已安装所有依赖包：`pip install -r requirements.txt`
- 检查Python版本是否为3.8或更高

### 问题2：找不到数据文件
- 确认数据文件路径设置正确
- 检查数据文件格式是否支持

### 问题3：图片无法保存
- 确认有数据输出目录的写入权限
- 检查磁盘空间是否充足

### 问题4：打包后文件过大
- **推荐使用 Windows 便携版**（体积更小）
- PyInstaller 打包可安装 UPX 进行压缩
- 参考 BUILD_README.md 中的优化步骤

### 问题5：便携版无法启动
- 检查杀毒软件是否拦截
- 尝试右键"以管理员身份运行"
- 查看 logs/ 目录中的日志文件

### 问题6：需要分发给没有Python的用户
- **使用 Windows 便携版**（推荐，约150MB）
- 或使用 PyInstaller 打包（约300-500MB）
- 两种方式都无需用户安装Python

## 📄 许可证

本项目采用 [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) 许可证（禁止商业使用）。

您可以自由地：
- 共享 — 复制和重新分发本作品
- 修改 — 重混、转换和基于本作品进行创作

但需遵守以下条款：
- **署名** — 必须给出适当的署名
- **非商业性使用** — 不得将本作品用于商业目的

## 👤 作者

FrankLaurance

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📮 联系方式

如有问题或建议，请通过GitHub Issues联系。
