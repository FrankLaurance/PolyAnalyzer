#!/bin/bash
# PyInstaller 打包脚本 - macOS/Linux
# 使用方法: chmod +x build.sh && ./build.sh

echo "================================"
echo "GPCtoPic PyInstaller 打包脚本"
echo "================================"

# 1. 清理之前的构建
echo "步骤 1/6: 清理旧的构建文件..."
rm -rf build dist *.spec.bak

# 2. 确认环境
echo "步骤 2/6: 检查 Python 环境..."
python --version
which python

# 3. 安装/更新 PyInstaller
echo "步骤 3/6: 检查 PyInstaller..."
pip show pyinstaller > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "安装 PyInstaller..."
    pip install pyinstaller
else
    echo "PyInstaller 已安装"
fi

# 4. 可选: 安装 UPX (压缩工具)
echo "步骤 4/6: 检查 UPX 压缩工具..."
which upx > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "警告: UPX 未安装,将跳过压缩步骤"
    echo "可通过 'brew install upx' 安装以减少体积"
    # 临时禁用 UPX
    sed -i.bak 's/upx=True/upx=False/' GPCtoPic.spec
else
    echo "UPX 已安装"
fi

# 5. 执行打包
echo "步骤 5/6: 开始打包..."
pyinstaller GPCtoPic.spec --clean

# 6. 显示结果
echo "步骤 6/6: 打包完成!"
if [ -f "dist/GPCtoPic" ]; then
    echo "================================"
    echo "✅ 打包成功!"
    echo "可执行文件: dist/GPCtoPic"
    echo "文件大小: $(du -h dist/GPCtoPic | cut -f1)"
    echo "================================"
    echo "运行方法:"
    echo "  cd dist"
    echo "  ./GPCtoPic"
    echo "================================"
else
    echo "❌ 打包失败,请检查错误信息"
    exit 1
fi
