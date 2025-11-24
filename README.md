# GPCtoPic - GPC数据可视化工具

一个用于处理和可视化GPC(凝胶渗透色谱)数据的Python工具，可以生成柱状图、分子量分布曲线和数据表格。

## ✨ 功能特点

- 📊 自动读取和处理GPC数据文件
- 📈 生成精美的柱状图和分子量分布曲线
- 📋 创建格式化的数据表格
- 🎨 支持自定义颜色、字体大小等样式
- 💾 批量导出高质量图片(PNG/PDF)
- 🖥️ 基于Streamlit的Web界面，操作简单直观
- 📦 支持多种打包方式，满足不同需求

## 🚀 快速开始

### 方式一：使用 Windows 便携版（推荐 - 无需安装Python）

**适合：完全不懂编程的用户**

1. 下载 `GPCtoPic_Windows_Portable_vX.X.zip`
2. 解压到任意位置
3. 双击 `启动应用.bat`
4. 浏览器自动打开，开始使用

✅ 优点：
- 无需安装任何软件
- 解压即用，体积约 150-200MB
- 支持读写本地文件
- 删除文件夹即完成卸载

### 方式二：直接运行Python脚本（开发者）

#### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/FrankLaurance/GPCtoPic.git
cd GPCtoPic

# 创建虚拟环境（推荐）
python -m venv myenv

# 激活虚拟环境
# macOS/Linux:
source myenv/bin/activate
# Windows:
myenv\Scripts\activate

# 安装依赖包
pip install -r requirements.txt
```

#### 2. 运行程序

```bash
streamlit run main.py
```

程序将自动在浏览器中打开，默认地址为 `http://localhost:8501`

### 方式三：使用 PyInstaller 打包版本

**适合：需要单文件分发的场景**

1. 下载 `GPCtoPic.exe`（从 Releases 页面）
2. 双击运行即可

⚠️ 注意：
- 文件较大（约 300-500MB）
- 可能被杀毒软件误报
- 首次启动较慢

### 📦 打包方式对比

| 方式 | 体积 | 用户体验 | 适用场景 |
|------|------|----------|----------|
| **Windows 便携版** | ~150MB | ⭐⭐⭐⭐⭐ | 推荐给普通用户 |
| **PyInstaller exe** | ~300-500MB | ⭐⭐⭐⭐ | 需要单文件分发 |
| **源码运行** | ~10MB | ⭐⭐⭐ | 开发者和技术用户 |

## 📖 使用说明

### 1. 准备数据文件

将GPC数据文件放在指定目录中

数据文件应包含以下列：
- 分子量相关数据 (Mn, Mw, Mz等)
- 分布数据 (PDI等)

### 2. 配置参数

在Web界面的侧边栏中，您可以配置：

**基本设置：**
- 数据目录路径
- 保存文件选项
- 生成图片选项

**样式设置：**
- 柱状图颜色
- 分子量曲线颜色
- 柱状图宽度
- 曲线宽度
- 坐标轴宽度

**字体设置：**
- 标题字体大小
- 坐标轴字体大小

**图表选项：**
- 是否绘制柱状图
- 是否绘制分子量曲线
- 是否生成数据表格
- 是否使用透明背景

### 3. 生成图表

1. 设置好参数后，点击"开始处理"按钮
2. 程序将自动处理数据目录中的所有文件
3. 生成的图片将保存在 `datapath` 目录下
4. 处理完成后可在界面中预览结果

### 4. 查看结果

- 点击"打开数据文件夹"按钮可直接打开保存图片的目录
- 所有生成的图片都会在界面中展示预览

## 🔧 配置文件

程序使用 `setting/defaultSetting.ini` 作为默认配置文件，包含以下参数：

```ini
[DEFAULT]
DataDir = datapath
SaveFile = True
BarWidth = 1.2
LineWidth = 1.0
AxisWidth = 1.0
TitleFontSize = 20
AxisFontSize = 14
TransparentBack = True
SavePicture = True
DisplayPicture = False
BarColor = #002FA7
MwColor = #FF6A07
DrawBar = True
DrawMw = True
DrawTable = True
```

您可以根据需要修改配置文件，或在Web界面中直接调整参数。

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
GPCtoPic_Windows_Portable_v1.0/
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
pyinstaller GPCtoPic.spec
```

生成的 exe 文件位于 `dist/GPCtoPic` 目录。

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

## 📋 依赖包

- streamlit >= 1.20.0
- numpy >= 1.20.0
- pandas >= 1.3.0
- matplotlib >= 3.5.0
- plottable >= 0.1.0
- openpyxl >= 3.0.0

## 🖥️ 系统要求

- Python 3.8+
- macOS / Windows / Linux

## 📝 项目结构

```
GPCtoPic/
├── main.py                    # 主程序文件
├── ui.py                      # Web界面
├── run_main.py               # 运行启动脚本
├── cnames.py                 # 中文名称映射
├── requirements.txt          # Python依赖
├── GPCtoPic.spec            # PyInstaller配置文件
├── package_windows.sh        # Windows便携版打包脚本
├── build.sh                  # macOS/Linux PyInstaller打包脚本
├── build.ps1                 # Windows PyInstaller打包脚本
├── BUILD_README.md          # 打包详细说明
├── main.ico                  # 程序图标
├── sinopec.jpg              # 页面图标
├── setting/                  # 配置文件目录
│   └── defaultSetting.ini
├── datapath/                 # 数据文件目录（输入）
├── GPC_output/              # GPC输出目录
├── Mw_output/               # 分子量输出目录
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
