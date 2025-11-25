# GPCtoPic - GPC Data Visualization Tool

A Python tool for processing and visualizing GPC (Gel Permeation Chromatography) data, capable of generating bar charts, molecular weight distribution curves, and data tables.

## ✨ Features

- 📊 Automatic reading and processing of GPC data files
- 📈 Generate beautiful bar charts and molecular weight distribution curves
- 📋 Create formatted data tables
- 🎨 Support custom colors, font sizes, and other styles
- 💾 Batch export high-quality images (PNG/PDF)
- 🖥️ Web interface based on Streamlit, simple and intuitive operation
- 🌍 Multi-language interface support (Chinese/English)
- 📦 Multiple packaging methods to meet different needs

## 🚀 Quick Start

### Method 1: Windows Portable Version (Recommended - No Python Required)

**For: Users with no programming experience**

1. Download `GPCtoPic_Windows_Portable_vX.X.zip`
2. Extract to any location
3. Double-click `启动应用.bat` (Start Application.bat)
4. Browser opens automatically, start using

✅ Advantages:
- No software installation required
- Extract and use, size ~150-200MB
- Supports reading/writing local files
- Delete folder to uninstall

### Method 2: Run Python Script Directly (Developers)

#### 1. Install Dependencies

```bash
# Clone project
git clone https://github.com/FrankLaurance/GPCtoPic.git
cd GPCtoPic

# Create virtual environment (recommended)
python -m venv myenv

# Activate virtual environment
# macOS/Linux:
source myenv/bin/activate
# Windows:
myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Run Program

```bash
streamlit run main.py
```

The program will automatically open in your browser at `http://localhost:8501`

### Method 3: PyInstaller Packaged Version

**For: Single-file distribution scenarios**

1. Download `GPCtoPic.exe` (from Releases page)
2. Double-click to run

⚠️ Note:
- Large file size (~300-500MB)
- May be flagged by antivirus software
- First startup is slow

### 📦 Packaging Method Comparison

| Method | Size | User Experience | Use Case |
|--------|------|-----------------|----------|
| **Windows Portable** | ~150MB | ⭐⭐⭐⭐⭐ | Recommended for regular users |
| **PyInstaller exe** | ~300-500MB | ⭐⭐⭐⭐ | Single-file distribution needed |
| **Source Code** | ~10MB | ⭐⭐⭐ | Developers and technical users |

## 📖 User Guide

### 0. Language Switching

The application supports Chinese (Simplified) and English interfaces:
1. After starting, click the sidebar
2. Select your language from the "Language" dropdown at the top
3. Interface will automatically refresh to the selected language

For details, see [I18N_README.md](I18N_README.md)

### 1. Prepare Data Files

Place GPC data files in the specified directory

Data files should contain the following columns:
- Molecular weight related data (Mn, Mw, Mz, etc.)
- Distribution data (PDI, etc.)

### 2. Configure Parameters

In the sidebar of the web interface, you can configure:

**Basic Settings:**
- Data directory path
- Save file options
- Generate image options

**Style Settings:**
- Bar chart color
- Molecular weight curve color
- Bar width
- Curve width
- Axis width

**Font Settings:**
- Title font size
- Axis font size

**Chart Options:**
- Draw bar chart
- Draw molecular weight curve
- Generate data table
- Use transparent background

### 3. Generate Charts

1. After setting parameters, click the "Run" button
2. Program will automatically process all files in the data directory
3. Generated images will be saved in the `datapath` directory
4. Results can be previewed in the interface after processing

### 4. View Results

- Click "Open Output Folder" button to directly open the directory with saved images
- All generated images will be displayed in the interface

## 🔧 Configuration File

The program uses `setting/defaultSetting.ini` as the default configuration file, containing the following parameters:

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

You can modify the configuration file as needed or adjust parameters directly in the web interface.

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
GPCtoPic_Windows_Portable_v1.0/
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
pyinstaller GPCtoPic.spec
```

Generated exe file located in `dist/GPCtoPic` directory.

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

## 📋 Dependencies

- streamlit >= 1.20.0
- numpy >= 1.20.0
- pandas >= 1.3.0
- matplotlib >= 3.5.0
- plottable >= 0.1.0
- openpyxl >= 3.0.0

## 🖥️ System Requirements

- Python 3.8+
- macOS / Windows / Linux

## 📝 Project Structure

```
GPCtoPic/
├── main.py                    # Main program file
├── ui.py                      # Web interface
├── i18n.py                    # Internationalization module
├── run_main.py               # Startup script
├── cnames.py                 # Chinese name mapping
├── requirements.txt          # Python dependencies
├── GPCtoPic.spec            # PyInstaller config
├── package_windows.sh        # Windows portable packaging script
├── build.sh                  # macOS/Linux PyInstaller script
├── build.ps1                 # Windows PyInstaller script
├── BUILD_README.md          # Packaging detailed instructions
├── I18N_README.md           # Internationalization documentation
├── main.ico                  # Program icon
├── sinopec.jpg              # Page icon
├── setting/                  # Configuration directory
│   ├── defaultSetting.ini   # Default settings
│   └── language.json        # Language preference (auto-generated)
├── datapath/                 # Data directory (input)
├── GPC_output/              # GPC output directory
├── Mw_output/               # Molecular weight output directory
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
