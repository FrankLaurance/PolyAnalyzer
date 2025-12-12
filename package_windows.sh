#!/bin/bash
# Windows 便携版打包脚本
# 注意：此脚本在 macOS/Linux 上运行，用于构建 Windows 便携版
# 使用方法: bash package_windows.sh

set -e  # 遇到错误立即退出

echo "======================================"
echo "  PolyAnalyzer Windows 便携版打包工具"
echo "======================================"
echo ""
echo "⚠️  注意："
echo "   - 此脚本在 macOS/Linux 上运行"
echo "   - 用于构建 Windows 便携版"
echo "   - 构建完成后需在 Windows 上测试"
echo ""

# 检查是否在 macOS/Linux 上运行
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "❌ 错误：此脚本不能在 Windows 上运行"
    echo "   请在 macOS 或 Linux 系统上运行此脚本"
    exit 1
fi

# 配置变量
APP_NAME="PolyAnalyzer"
# 从 main.py 获取版本号
VERSION=$(grep 'APP_VERSION =' main.py | cut -d '"' -f 2)
if [ -z "$VERSION" ]; then
    VERSION="1.0"
    echo "Warning: Could not detect version from main.py, using default: $VERSION"
else
    echo "Detected version: $VERSION"
fi

PYTHON_VERSION="3.11.9"  # 使用稳定版本
PYTHON_EMBED_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-embed-amd64.zip"
OUTPUT_DIR="dist_portable_windows"
PACKAGE_NAME="${APP_NAME}_Windows_Portable_v${VERSION}"
CACHE_DIR="build_cache"

# 准备缓存目录
if [ ! -d "$CACHE_DIR" ]; then
    mkdir -p "$CACHE_DIR"
fi

# 预先下载文件到缓存
echo "[0/8] 检查并下载依赖文件到缓存..."

# 检查/下载 Python
if [ -f "$CACHE_DIR/python_embed.zip" ]; then
    echo "   - Python 嵌入式包已存在于缓存"
else
    echo "   - 下载 Python 嵌入式版本 (${PYTHON_VERSION})..."
    if ! curl -L -o "$CACHE_DIR/python_embed.zip" "$PYTHON_EMBED_URL"; then
        echo "❌ 下载失败！请检查网络连接"
        exit 1
    fi
fi

# 检查/下载 get-pip.py
if [ -f "$CACHE_DIR/get-pip.py" ]; then
    echo "   - get-pip.py 已存在于缓存"
else
    echo "   - 下载 pip 安装器..."
    curl -L -o "$CACHE_DIR/get-pip.py" https://bootstrap.pypa.io/get-pip.py
fi

# 清理旧的输出目录
if [ -d "$OUTPUT_DIR" ]; then
    echo "[1/8] 清理旧的构建目录..."
    rm -rf "$OUTPUT_DIR"
fi

# 创建输出目录结构
echo "[2/8] 创建目录结构..."
mkdir -p "$OUTPUT_DIR/$PACKAGE_NAME"
cd "$OUTPUT_DIR/$PACKAGE_NAME"

# 解压 Python
echo "[3/8] 从缓存解压 Python..."
unzip -q "../../$CACHE_DIR/python_embed.zip" -d python

# 复制 get-pip.py
echo "[4/8] 从缓存复制 pip 安装器..."
cp "../../$CACHE_DIR/get-pip.py" .

# 获取 Python 主版本和次版本
PY_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PY_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
PTH_FILENAME="python${PY_MAJOR}${PY_MINOR}._pth"

# 修改 python._pth 文件以启用 site-packages
echo "[5/8] 配置 Python 环境..."
PTH_FILE="python/$PTH_FILENAME"

if [ ! -f "$PTH_FILE" ]; then
    echo "Warning: Expected ._pth file not found at $PTH_FILE"
    # 尝试查找任何 ._pth 文件
    FOUND_PTH=$(find python -name "*._pth" | head -n 1)
    if [ -n "$FOUND_PTH" ]; then
        echo "Found alternative ._pth file: $FOUND_PTH"
        PTH_FILE="$FOUND_PTH"
        PTH_FILENAME=$(basename "$FOUND_PTH")
    fi
fi

if [ -f "$PTH_FILE" ]; then
    # 显示原始内容
    echo "Original ._pth file:"
    cat "$PTH_FILE"
    
    # 完全重写 ._pth 文件以确保正确配置
    cat > "$PTH_FILE" << 'PTHEOF'
python311.zip
.
Lib/site-packages

# Uncomment to run site.main() automatically
import site
PTHEOF
    
    # 显示修改后的内容
    echo ""
    echo "Modified ._pth file:"
    cat "$PTH_FILE"
else
    echo "Warning: ._pth file not found at $PTH_FILE"
fi

# 创建 Lib 目录结构
echo "Creating directory structure..."
mkdir -p "python/Lib/site-packages"
mkdir -p "python/Scripts"

echo "[6/8] 跳过包安装（需在 Windows 上完成）..."

# 复制应用文件
echo "[8/8] 复制应用文件..."
cd ../..
cp main.py "$OUTPUT_DIR/$PACKAGE_NAME/"
cp ui.py "$OUTPUT_DIR/$PACKAGE_NAME/"
cp i18n.py "$OUTPUT_DIR/$PACKAGE_NAME/"
cp cnames.py "$OUTPUT_DIR/$PACKAGE_NAME/"
cp run_main.py "$OUTPUT_DIR/$PACKAGE_NAME/"
cp requirements.txt "$OUTPUT_DIR/$PACKAGE_NAME/"
cp README.md "$OUTPUT_DIR/$PACKAGE_NAME/"
cp README_EN.md "$OUTPUT_DIR/$PACKAGE_NAME/"
cp LICENSE "$OUTPUT_DIR/$PACKAGE_NAME/" 2>/dev/null || true

# 复制必要的目录
cp -r setting "$OUTPUT_DIR/$PACKAGE_NAME/"
cp -r datapath "$OUTPUT_DIR/$PACKAGE_NAME/"
mkdir -p "$OUTPUT_DIR/$PACKAGE_NAME/GPC_output"
mkdir -p "$OUTPUT_DIR/$PACKAGE_NAME/Mw_output"
mkdir -p "$OUTPUT_DIR/$PACKAGE_NAME/logs"

# 复制图标资源（如果存在）
cp main.ico "$OUTPUT_DIR/$PACKAGE_NAME/" 2>/dev/null || echo "   Warning: main.ico not found, skipping..."

# 创建安装脚本（在 Windows 上运行）
cat > "$OUTPUT_DIR/$PACKAGE_NAME/install_dependencies.bat" << 'EOF'
@echo off
chcp 65001 >nul
title Install Dependencies

echo ====================================
echo   Installing Python Dependencies
echo ====================================
echo.

:: Check if Python exists
if not exist "%~dp0python\python.exe" (
    echo [ERROR] Python not found in python folder!
    pause
    exit /b 1
)

echo [Step 0] Checking Python configuration...
"%~dp0python\python.exe" --version
echo.

:: Check if already installed
echo [Step 1] Checking existing installation...
set NEED_INSTALL=0

"%~dp0python\python.exe" -c "import streamlit" 2>nul
if errorlevel 1 (
    echo [INFO] streamlit not installed
    set NEED_INSTALL=1
) else (
    echo [OK] streamlit already installed
)

"%~dp0python\python.exe" -c "import numpy" 2>nul
if errorlevel 1 (
    echo [INFO] numpy not installed
    set NEED_INSTALL=1
) else (
    echo [OK] numpy already installed
)

"%~dp0python\python.exe" -c "import pandas" 2>nul
if errorlevel 1 (
    echo [INFO] pandas not installed
    set NEED_INSTALL=1
) else (
    echo [OK] pandas already installed
)

"%~dp0python\python.exe" -c "import matplotlib" 2>nul
if errorlevel 1 (
    echo [INFO] matplotlib not installed
    set NEED_INSTALL=1
) else (
    echo [OK] matplotlib already installed
)

if %NEED_INSTALL%==0 (
    echo.
    echo ====================================
    echo   All packages already installed!
    echo ====================================
    echo.
    echo You can run "Start_App.bat" to start the application.
    echo If you want to reinstall, delete the python\Lib\site-packages folder first.
    echo.
    pause
    exit /b 0
)

echo.
echo [Step 2] Checking pip...
"%~dp0python\python.exe" -m pip --version 2>nul
if errorlevel 1 (
    echo [INFO] pip not installed, installing now...
    
    :: Display Python path configuration
    if exist "%~dp0python\python311._pth" (
        echo Current ._pth file:
        type "%~dp0python\python311._pth"
        echo.
    )
    
    if not exist "%~dp0get-pip.py" (
        echo [ERROR] get-pip.py not found!
        pause
        exit /b 1
    )
    
    "%~dp0python\python.exe" get-pip.py --no-warn-script-location
    if errorlevel 1 (
        echo [ERROR] Failed to install pip!
        pause
        exit /b 1
    )
    
    :: Wait a moment for files to be written
    timeout /t 2 /nobreak >nul
    
    echo [Step 3] Testing pip import...
    "%~dp0python\python.exe" -c "import pip; print('[OK] pip version:', pip.__version__)"
    if errorlevel 1 goto :fix_pip_error
) else (
    "%~dp0python\python.exe" -m pip --version
    echo [OK] pip is ready
)

goto :install_tools

:fix_pip_error
echo [ERROR] Cannot import pip module!
echo.
echo Auto-fixing Python configuration...

:: Create correct pth file
(
    echo python311.zip
    echo .
    echo Lib\site-packages
    echo Scripts
    echo.
    echo # Enable site module
    echo import site
) > "%~dp0python\python311._pth"

echo Fixed. Please close and run this script again.
pause
exit /b 1

:install_tools
echo.
echo [Step 4] Upgrading pip and installing tools...
"%~dp0python\python.exe" -m pip install --upgrade pip setuptools wheel --no-warn-script-location

echo.
echo [Step 5] Installing application dependencies...
echo This may take 5-10 minutes, please be patient...
echo Installing: streamlit numpy pandas matplotlib plottable openpyxl
echo.

"%~dp0python\python.exe" -m pip install -r requirements.txt --no-warn-script-location
if errorlevel 1 (
    echo.
    echo [WARNING] Batch installation had issues, trying individual packages...
    echo.
    "%~dp0python\python.exe" -m pip install streamlit --no-warn-script-location
    "%~dp0python\python.exe" -m pip install numpy --no-warn-script-location
    "%~dp0python\python.exe" -m pip install pandas --no-warn-script-location
    "%~dp0python\python.exe" -m pip install matplotlib --no-warn-script-location
    "%~dp0python\python.exe" -m pip install plottable --no-warn-script-location
    "%~dp0python\python.exe" -m pip install openpyxl --no-warn-script-location
)

echo.
echo ====================================
echo   Installation Complete!
echo ====================================
echo.
echo Verifying packages:
echo.
"%~dp0python\python.exe" -c "import streamlit; print('[OK] streamlit', streamlit.__version__)" 2>nul || echo [FAIL] streamlit
"%~dp0python\python.exe" -c "import numpy; print('[OK] numpy', numpy.__version__)" 2>nul || echo [FAIL] numpy
"%~dp0python\python.exe" -c "import pandas; print('[OK] pandas', pandas.__version__)" 2>nul || echo [FAIL] pandas
"%~dp0python\python.exe" -c "import matplotlib; print('[OK] matplotlib', matplotlib.__version__)" 2>nul || echo [FAIL] matplotlib

echo.
echo If all packages show [OK], you can run "Start_App.bat"
echo Otherwise, run "Check_Installation.bat" for more details
echo.
pause
EOF

# 创建启动脚本
cat > "$OUTPUT_DIR/$PACKAGE_NAME/Start_App.bat" << 'EOF'
@echo off
chcp 65001 >nul
title PolyAnalyzer - Polymer Data Analysis Tool

echo ====================================
echo   Starting PolyAnalyzer...
echo ====================================
echo.

:: Set environment variables
set PYTHONPATH=%~dp0
set MPLBACKEND=Agg

:: Check if Python exists
if not exist "%~dp0python\python.exe" (
    echo [ERROR] Python environment not found!
    echo Please make sure the python folder exists.
    pause
    exit /b 1
)

:: Check if streamlit is installed
"%~dp0python\python.exe" -c "import streamlit" 2>nul
if errorlevel 1 (
    echo [ERROR] Streamlit not installed!
    echo.
    echo Please run "install_dependencies.bat" first to install required packages.
    echo.
    pause
    exit /b 1
)

:: Start application
echo [INFO] Starting Streamlit application...
echo [INFO] Browser will open automatically
echo [INFO] To stop the application, close this window
echo.
echo ====================================
echo.

"%~dp0python\python.exe" -m streamlit run "%~dp0main.py" --server.headless=false

:: If startup fails
if errorlevel 1 (
    echo.
    echo [ERROR] Application failed to start!
    echo Please check the log files for details.
    pause
)
EOF

# 创建命令行启动脚本（用于调试）
cat > "$OUTPUT_DIR/$PACKAGE_NAME/Command_Line.bat" << 'EOF'
@echo off
chcp 65001 >nul

echo ====================================
echo   PolyAnalyzer Command Line Mode
echo ====================================
echo.
echo You can now use Python commands
echo Example: python run_main.py
echo.

set PYTHONPATH=%~dp0
set PATH=%~dp0python;%~dp0python\Scripts;%PATH%

cmd /k "cd /d %~dp0"
EOF

# 创建诊断脚本
cat > "$OUTPUT_DIR/$PACKAGE_NAME/Check_Installation.bat" << 'EOF'
@echo off
chcp 65001 >nul
title Check Installation

echo ====================================
echo   Checking Installation
echo ====================================
echo.

:: Check Python
echo [1/4] Checking Python...
if exist "%~dp0python\python.exe" (
    echo [OK] Python found
    "%~dp0python\python.exe" --version
) else (
    echo [ERROR] Python not found!
    goto :end
)

echo.
echo [2/4] Checking pip...
"%~dp0python\python.exe" -m pip --version
if errorlevel 1 (
    echo [ERROR] pip not installed!
    echo Please run install_dependencies.bat
    goto :end
)

echo.
echo [3/4] Checking installed packages...
"%~dp0python\python.exe" -m pip list

echo.
echo [4/4] Checking required packages...
echo Checking streamlit...
"%~dp0python\python.exe" -c "import streamlit; print('streamlit version:', streamlit.__version__)" 2>nul
if errorlevel 1 (
    echo [ERROR] streamlit not installed!
) else (
    echo [OK] streamlit installed
)

echo.
echo Checking numpy...
"%~dp0python\python.exe" -c "import numpy; print('numpy version:', numpy.__version__)" 2>nul
if errorlevel 1 (
    echo [ERROR] numpy not installed!
) else (
    echo [OK] numpy installed
)

echo.
echo Checking pandas...
"%~dp0python\python.exe" -c "import pandas; print('pandas version:', pandas.__version__)" 2>nul
if errorlevel 1 (
    echo [ERROR] pandas not installed!
) else (
    echo [OK] pandas installed
)

echo.
echo Checking matplotlib...
"%~dp0python\python.exe" -c "import matplotlib; print('matplotlib version:', matplotlib.__version__)" 2>nul
if errorlevel 1 (
    echo [ERROR] matplotlib not installed!
) else (
    echo [OK] matplotlib installed
)

echo.
echo ====================================
echo   Check Complete
echo ====================================

:end
echo.
pause
EOF

# 创建卸载说明
cat > "$OUTPUT_DIR/$PACKAGE_NAME/How_to_Uninstall.txt" << 'EOF'
PolyAnalyzer Portable Version - Uninstallation Guide
================================================

This is a portable application with no system installation.

Uninstall Method:
1. Close the running application (if any)
2. Simply delete the entire folder

All data is stored within this folder:
- datapath/     : Input data
- GPC_output/   : GPC output results
- Mw_output/    : Molecular weight output
- logs/         : Log files
- setting/      : Configuration files

To backup your data, please copy the above folders.
EOF

# 创建使用说明
cat > "$OUTPUT_DIR/$PACKAGE_NAME/USER_GUIDE_EN.txt" << 'EOF'
PolyAnalyzer Windows Portable Version - User Guide
===============================================

Quick Start (First Time Use)
-----------------------------
1. Double-click "install_dependencies.bat" to install dependencies (first time only, requires internet)
2. Wait for installation to complete (takes about 3-5 minutes)
3. Double-click "Start_App.bat" to launch the program
4. Browser will open automatically (usually at http://localhost:8501)

Subsequent Use
--------------
After installing dependencies, simply:
1. Double-click "Start_App.bat"
2. Start using the application

Folder Structure
----------------
- datapath/     : Place .rst data files here
- GPC_output/   : GPC processing results output location
- Mw_output/    : Molecular weight data output location
- setting/      : Configuration files storage
- logs/         : Application log files
- python/       : Python runtime environment (DO NOT DELETE)

Frequently Asked Questions
--------------------------
Q: Application won't start?
A: 1. Check if antivirus software is blocking it
   2. Try right-click "Run as administrator"
   3. Check log files in the logs/ folder

Q: Browser doesn't open automatically?
A: Manually open your browser and visit http://localhost:8501

Q: How to stop the application?
A: Close the command line window

Q: Can I move the folder to another location?
A: Yes, the entire folder can be moved anywhere

Technical Support
-----------------
GitHub: https://github.com/FrankLaurance/PolyAnalyzer
Issue Reporting: Submit an issue on GitHub

Version Information
-------------------
Application Version: ${VERSION}
Python Version: 3.11.9
EOF

# 创建使用说明
cat > "$OUTPUT_DIR/$PACKAGE_NAME/USER_GUIDE.txt" << 'EOF'
PolyAnalyzer Windows 便携版使用说明
================================

1. 首次使用
-----------
双击 "install_dependencies.bat" 安装依赖（需联网，仅需运行一次）。

2. 启动软件
-----------
双击 "Start_App.bat"，打开软件。

3. 使用方法
-----------
- 将 .rst 数据文件放入 datapath 文件夹。
- 在网页界面中选择文件并运行分析。

4. 结果查看
-----------
- GPC 结果：GPC_output 文件夹
- 分子量结果：Mw_output 文件夹

5. 常见问题
-----------
- 如果浏览器未自动打开，请手动访问：http://localhost:8501
- 关闭黑色命令行窗口即可退出程序。
EOF

# 压缩打包
echo ""
echo "======================================"
echo "  Package Complete!"
echo "======================================"
echo ""
echo "⚠️  IMPORTANT: Steps to Complete Windows Portable Version"
echo ""
echo "1. On Windows System:"
echo "   - Copy $OUTPUT_DIR/$PACKAGE_NAME folder to Windows"
echo "   - Double-click install_dependencies.bat to install dependencies"
echo "   - Double-click Start_App.bat to test"
echo ""
echo "2. Package for Distribution:"
echo "   - After successful installation, compress the entire folder"
echo "   - When distributing, users don't need to install dependencies again"
echo ""
echo "Output Directory: $OUTPUT_DIR/$PACKAGE_NAME"
echo ""

# Optional: Automatically create zip package
read -p "Create ZIP package now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Compressing..."
    cd "$OUTPUT_DIR"
    zip -r -q "${PACKAGE_NAME}.zip" "$PACKAGE_NAME"
    cd ..
    echo "✅ ZIP package created: ${OUTPUT_DIR}/${PACKAGE_NAME}.zip"
    
    # Display file size
    SIZE=$(du -h "${OUTPUT_DIR}/${PACKAGE_NAME}.zip" | cut -f1)
    echo "📦 File size: $SIZE"
fi

echo ""
echo "✅ All Done!"
