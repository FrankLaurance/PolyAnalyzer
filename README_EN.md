# PolyAnalyzer - Polymer Materials Data Visualization Tool

English | [中文](README.md)

A professional data analysis and visualization tool for polymer materials, integrating GPC (Gel Permeation Chromatography) and DSC (Differential Scanning Calorimetry) analysis capabilities, providing researchers with efficient and intuitive data processing experience.

## ✨ Core Features

### 📊 GPC Gel Permeation Chromatography Analysis
- Automatic reading and processing of GPC data files
- Generate beautiful bar charts and molecular weight distribution curves
- Create professional molecular weight data tables
- Batch processing of multiple sample data

### 🔥 DSC Differential Scanning Calorimetry Analysis
- Automatic recognition and parsing of DSC heat flow data
- Intelligent extraction of multi-cycle test data
- Draw heat flow vs. temperature curves
- Support automatic peak detection and centering display
- Multi-cycle data comparison analysis
- Data segmentation saving and visualization

### 🎨 General Features
- Support custom colors, line widths, font sizes and other styles
- Batch export high-quality images (PNG, 300 DPI)
- Modern web interface based on Streamlit
- Multi-language interface support (Chinese/English)
- Flexible configuration management system
- Complete logging functionality
- Multiple packaging methods to meet different deployment needs

## 🚀 Quick Start

### Method 1: Windows Portable Version (Recommended - Zero Barrier to Entry)

**Target Users: Researchers, Laboratory Users, Non-programmers**

#### Usage Steps:
1. Download the latest `PolyAnalyzer_Windows_Portable_vX.X.X.zip` from [Releases](https://github.com/FrankLaurance/PolyAnalyzer/releases)
2. Extract to any location (paths without Chinese characters and spaces recommended)
3. Double-click `启动应用.bat` or `Start_App.bat`
4. Browser automatically opens the application interface, ready to use

#### Features:
- ✅ Completely portable and installation-free, no Python environment configuration needed
- ✅ All dependencies included, size approximately 150-200MB
- ✅ Full support for local file read/write operations
- ✅ Uninstall by simply deleting the folder
- ✅ Offline usage supported, data security guaranteed

### Method 2: Run from Source Code (Developers & Technical Users)

**Target Users: Developers, Users Needing Customization, Cross-platform Usage**

#### System Requirements:
- Python 3.8 or higher
- pip package manager

#### Installation Steps:

```bash
# 1. Clone the project repository
git clone https://github.com/FrankLaurance/PolyAnalyzer.git
cd PolyAnalyzer

# 2. Create virtual environment (strongly recommended)
python -m venv myenv

# 3. Activate virtual environment
# macOS/Linux:
source myenv/bin/activate
# Windows:
myenv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
```

#### Run Program:

```bash
# Method 1: Run directly with Streamlit
streamlit run main.py

# Method 2: Use the project's run script
python run_main.py
```

The program will automatically open in your browser at `http://localhost:8501`

### Method 3: PyInstaller Single-File Version (Build It Yourself)

**Target Users: Scenarios Requiring Single-File Distribution, Simplified Deployment**

#### Build Steps:

**Prerequisites:**
```bash
# Ensure project dependencies are installed
pip install -r requirements.txt
```

**Automatic Build (Recommended):**
```bash
# macOS/Linux
chmod +x build.sh
./build.sh

# Windows
.\build.ps1
```

**Manual Build:**
```bash
pip install pyinstaller
pyinstaller PolyAnalyzer.spec
```

The generated `PolyAnalyzer.exe` is located in the `dist/PolyAnalyzer/` directory

> 💡 **Note:** Build scripts will automatically install PyInstaller, but will not install project dependencies. Please ensure you run `pip install -r requirements.txt` first.

#### Usage Instructions:
1. Distribute the generated exe file to users
2. Users can run it by double-clicking, no installation required

#### Notes:
- ⚠️ Large file size (approximately 300-500MB), contains complete runtime environment
- ⚠️ First startup requires decompression cache, startup time about 10-30 seconds
- ⚠️ Some antivirus software may flag false positives, add to trust or use portable version
- ℹ️ For detailed packaging instructions, see [BUILD_README.md](BUILD_README.md)

### 📦 Deployment Method Comparison

| Method | Size | Startup Speed | User Experience | Target Users | Cross-Platform |
|--------|------|---------------|-----------------|--------------|----------------|
| **Windows Portable** | ~150MB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Lab users, Researchers | Windows |
| **Source Code** | ~10MB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Developers, Technical users | All Platforms |
| **PyInstaller exe** | ~300-500MB | ⭐⭐⭐ | ⭐⭐⭐ | Single-file distribution | Windows |

## 📖 User Guide

### 0. Language Switching

The application supports **Chinese (Simplified)** and **English** bilingual interface:
1. After starting the app, find the **"语言/Language"** dropdown menu at the top of the left sidebar
2. Select your preferred language
3. The interface will automatically refresh and switch to the selected language

For detailed internationalization instructions, see: [I18N_README.md](I18N_README.md)

### 1. Prepare Data Files

#### GPC Data File Requirements:
- Supported formats: `.txt`, `.csv` and other text files
- Required data columns:
  - Molecular weight data: Mn (Number average), Mw (Weight average), Mz (Z-average)
  - Distribution index: PDI (Polydispersity index)
  - Molecular weight distribution curve data

#### DSC Data File Requirements:
- Supported formats: `.txt` or `.rst` files exported from TA instruments
- Files should contain:
  - Heat Flow data
  - Temperature data
  - Time data
  - Method information (for automatic cycle recognition)

### 2. Configure Parameters

The application provides rich configuration options in the sidebar of the web interface:

#### GPC Analysis Configuration:

**Basic Settings:**
- 📁 Data directory path
- 💾 CSV file save options
- 🖼️ Image generation and save options

**Style Settings:**
- 🎨 Bar chart color (Default: #002FA7)
- 🎨 Molecular weight curve color (Default: #FF6A07)
- 📏 Bar width
- 📏 Curve line width
- 📏 Axis thickness

**Font Settings:**
- 📝 Title font size
- 📝 Axis font size

**Chart Options:**
- ☑️ Draw bar chart
- ☑️ Draw molecular weight curve
- ☑️ Generate data table
- ☑️ Use transparent background

#### DSC Analysis Configuration:

**Basic Settings:**
- 📁 DSC data directory path
- 💾 Segmented data save options
- 🖼️ Cycle comparison plot save options

**Analysis Parameters:**
- 📊 Left and right boundary range (for peak display range)
- 🔍 Peak detection parameters

**Plot Options:**
- ☑️ Save segmented data (CSV format)
- ☑️ Draw segmented plots
- ☑️ Draw cycle comparison plots
- ☑️ Automatic peak centering display

**Style Settings:**
- 🎨 Curve color
- 📏 Line width
- 📏 Axis thickness
- 📝 Font size settings

### 3. Run Analysis

#### GPC Analysis Workflow:
1. Select or enter data directory path in the sidebar
2. Adjust parameters and style settings as needed
3. Click the **"Start Processing"** or **"Run"** button
4. Program will automatically process all data files in the directory
5. Processing progress is displayed in real-time on the interface
6. After completion, processing time and result preview are shown

#### DSC Analysis Workflow:
1. Switch to the **"DSC Analysis"** tab
2. Select DSC data directory
3. Configure analysis parameters (number of cycles, peak detection parameters, etc.)
4. Click the **"Run"** button to start analysis
5. The program will automatically:
   - Recognize multi-cycle data
   - Extract heat flow-temperature data for each cycle
   - Save segmented data as CSV files
   - Generate individual curve plots for each cycle
   - Generate cycle comparison overlay plots

### 4. View and Export Results

#### Output File Locations:
- **GPC Results:** 
  - Images: `datapath/SampleName/` folder
  - CSV data: `GPC_output/` folder
  - Molecular weight summary: `Mw_output/` folder

- **DSC Results:**
  - Cycle data: `DSC_Cycle/CycleX/` folder (CSV format)
  - Curve plots: `DSC_Pic/SampleName/` folder (PNG format)
  - Cycle comparison plots: `result.png` in each Cycle folder

#### Convenient Operations:
- Click the **"Open Output Folder"** button to directly access the results directory
- All generated images are previewed in real-time on the interface
- Support viewing and downloading images directly in the browser

## 🔧 Configuration File Description

### GPC Configuration File

The program uses `setting/defaultSetting.ini` as the default configuration file for GPC analysis:

```ini
[DEFAULT]
# Basic Settings
DataDir = datapath                # Data directory
SaveFile = True                   # Whether to save CSV files
SavePicture = True                # Whether to save images
DisplayPicture = False            # Whether to display images in interface

# Graphic Styles
BarColor = #002FA7                # Bar chart color (dark blue)
MwColor = #FF6A07                 # Molecular weight curve color (orange)
BarWidth = 1.2                    # Bar width
LineWidth = 1.0                   # Curve line width
AxisWidth = 1.0                   # Axis thickness

# Font Settings
TitleFontSize = 20                # Title font size
AxisFontSize = 14                 # Axis font size

# Chart Options
DrawBar = True                    # Draw bar chart
DrawMw = True                     # Draw molecular weight curve
DrawTable = True                  # Generate data table
TransparentBack = True            # Use transparent background
```

### DSC Configuration File

The program uses `setting/defaultDSCSetting.ini` as the default configuration file for DSC analysis:

```ini
[DEFAULT]
# Curve Styles
curve_color = #002FA7             # Curve color
line_width = 1.0                  # Line width
axis_width = 1.0                  # Axis thickness

# Font Settings
title_font_size = 20              # Title font size
axis_font_size = 14               # Axis font size

# Graphic Options
transparent_back = True           # Use transparent background
```

### Configuration Management

- ✏️ Can directly edit INI files to modify default configurations
- 💾 Can save modified parameters as new configuration schemes in the web interface
- 📋 Support multiple configuration scheme management, can switch anytime
- 🔄 Support deleting custom configurations, restoring default settings

## 📦 Packaging Instructions

### Method 1: Package Windows Portable Version (Recommended)

**Features: Small size, green portable, best user experience**

```bash
# Execute on macOS/Linux
bash package_windows.sh
```

The script will automatically:
1. Download Python embedded version
2. Install all dependencies
3. Create startup scripts
4. Package into ZIP file

Generated file structure:
```
PolyAnalyzer_Windows_Portable_v1.0/
├── 启动应用.bat          # User double-click to start
├── python/               # Embedded Python environment
├── main.py              # Application code
├── datapath/            # Data directory
└── 使用说明.txt          # User documentation
```

**Advantages:**
- ✅ Size ~150-200MB (50% smaller than PyInstaller)
- ✅ Fully green portable, no installation required
- ✅ Supports reading/writing local files
- ✅ Good user experience, double-click to use

### Method 2: PyInstaller Packaging

**Features: Single exe file, but larger size**

**Automatic packaging script:**

```bash
# macOS/Linux
chmod +x build.sh
./build.sh

# Windows
.\build.ps1
```

**Manual packaging:**

```bash
pip install pyinstaller
pyinstaller PolyAnalyzer.spec
```

Generated exe file located in `dist/PolyAnalyzer` directory.

**Notes:**
- Large file size (300-500MB)
- May require UPX compression
- See [BUILD_README.md](BUILD_README.md) for details

### Packaging Method Selection Guide

| Scenario | Recommended Method | Reason |
|----------|-------------------|---------|
| Distribute to regular users | **Windows Portable** | Small size, good user experience |
| Single file needed | PyInstaller | Easy to distribute and manage |
| Development/Testing | Source code | Flexible and convenient |

## 📋 Main Dependencies

### Core Dependencies
- **streamlit** >= 1.20.0 - Web interface framework
- **numpy** >= 1.20.0 - Numerical computing
- **pandas** >= 1.3.0 - Data processing
- **matplotlib** >= 3.5.0 - Plotting

### Functional Dependencies
- **plottable** >= 0.1.0 - Table plotting
- **scipy** >= 1.7.0 - Scientific computing (DSC peak detection)
- **chardet** >= 4.0.0 - File encoding detection

For complete dependency list, see [requirements.txt](requirements.txt)

## 🖥️ System Requirements

### Running from Source
- **Python Version:** 3.8 or higher
- **Operating System:** Windows / macOS / Linux
- **RAM:** At least 2GB
- **Disk Space:** At least 500MB (including data files)

### Windows Portable Version
- **Operating System:** Windows 7 or higher
- **RAM:** At least 2GB
- **Disk Space:** At least 500MB (including program and data)

## 📝 Project Structure

```
PolyAnalyzer/
├── main.py                    # Main program file (includes GPC/DSC/Mw analyzers)
├── ui.py                      # Streamlit web interface
├── i18n.py                    # Internationalization module (multi-language support)
├── run_main.py               # Run startup script
├── cnames.py                 # Color name mapping
├── requirements.txt          # Python dependency list
├── PolyAnalyzer.spec            # PyInstaller packaging config
├── package_windows.sh        # Windows portable packaging script
├── build.sh / build.ps1     # PyInstaller packaging scripts
├── BUILD_README.md          # Detailed packaging documentation
├── I18N_README.md           # Internationalization documentation
├── OPTIMIZATION_REPORT.md   # Optimization report
├── README.md / README_EN.md # Project documentation
├── setting/                  # Configuration files directory
│   ├── defaultSetting.ini   # GPC default configuration
│   ├── defaultDSCSetting.ini # DSC default configuration
│   └── language.json        # Language preference (auto-generated)
├── datapath/                 # GPC data files directory (input)
├── GPC_output/              # GPC analysis results output
├── Mw_output/               # Molecular weight summary output
├── DSC_Cycle/               # DSC cycle data output
├── DSC_Pic/                 # DSC graphics output
└── logs/                     # Log files directory
```

## 🐛 Troubleshooting

### Issue 1: Program won't start
- Confirm all dependencies are installed: `pip install -r requirements.txt`
- Check Python version is 3.8 or higher

### Issue 2: Can't find data files
- Confirm data file path is set correctly
- Check if data file format is supported

### Issue 3: Can't save images
- Confirm you have write permission to data output directory
- Check if disk space is sufficient

### Issue 4: Packaged file too large
- **Recommend using Windows Portable version** (smaller size)
- PyInstaller packaging can install UPX for compression
- Refer to BUILD_README.md for optimization steps

### Issue 5: Portable version won't start
- Check if antivirus software is blocking
- Try right-click "Run as administrator"
- Check log files in logs/ directory

### Issue 6: Need to distribute to users without Python
- **Use Windows Portable version** (recommended, ~150MB)
- Or use PyInstaller packaging (~300-500MB)
- Both methods don't require users to install Python

## 📄 License

This project is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) (Non-Commercial Use Only).

You are free to:
- Share — copy and redistribute the work
- Adapt — remix, transform, and build upon the work

Under the following terms:
- **Attribution** — Must give appropriate credit
- **NonCommercial** — Cannot use for commercial purposes

## 👤 Author

FrankLaurance

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📮 Contact

For questions or suggestions, please contact via GitHub Issues.
