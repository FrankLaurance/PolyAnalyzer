# PyInstaller 打包脚本 - Windows
# 使用方法: 在 PowerShell 中运行 .\build.ps1

Write-Host "================================"
Write-Host "GPCtoPic PyInstaller 打包脚本"
Write-Host "================================"

# 1. 清理之前的构建
Write-Host "步骤 1/6: 清理旧的构建文件..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# 2. 确认环境
Write-Host "步骤 2/6: 检查 Python 环境..."
python --version
python -c "import sys; print(sys.executable)"

# 3. 安装/更新 PyInstaller
Write-Host "步骤 3/6: 检查 PyInstaller..."
$pyinstallerCheck = pip show pyinstaller 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "安装 PyInstaller..."
    pip install pyinstaller
} else {
    Write-Host "PyInstaller 已安装"
}

# 4. 检查 UPX
Write-Host "步骤 4/6: 检查 UPX 压缩工具..."
$upxCheck = Get-Command upx -ErrorAction SilentlyContinue
if (-not $upxCheck) {
    Write-Host "警告: UPX 未安装,将跳过压缩步骤"
    Write-Host "可从 https://upx.github.io/ 下载以减少体积"
    # 临时禁用 UPX
    (Get-Content GPCtoPic.spec) -replace 'upx=True', 'upx=False' | Set-Content GPCtoPic.spec
} else {
    Write-Host "UPX 已安装"
}

# 5. 执行打包
Write-Host "步骤 5/6: 开始打包..."
pyinstaller GPCtoPic.spec --clean

# 6. 显示结果
Write-Host "步骤 6/6: 打包完成!"
if (Test-Path "dist\GPCtoPic.exe") {
    Write-Host "================================"
    Write-Host "✅ 打包成功!"
    Write-Host "可执行文件: dist\GPCtoPic.exe"
    $fileSize = (Get-Item "dist\GPCtoPic.exe").Length / 1MB
    Write-Host "文件大小: $([math]::Round($fileSize, 2)) MB"
    Write-Host "================================"
    Write-Host "运行方法:"
    Write-Host "  cd dist"
    Write-Host "  .\GPCtoPic.exe"
    Write-Host "================================"
} else {
    Write-Host "❌ 打包失败,请检查错误信息"
    exit 1
}
