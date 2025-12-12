# PyInstaller 打包脚本 - Windows
# 使用方法: 在 PowerShell 中运行 .\build.ps1

Write-Host "================================"
Write-Host "PolyAnalyzer PyInstaller 打包脚本"
Write-Host "================================"

# 1. 清理之前的构建
Write-Host "步骤 1/6: 清理旧的构建文件..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# 2. 确认环境
Write-Host "步骤 2/6: 检查 Python 环境..."
python --version
python -c "import sys; print(sys.executable)"

# 获取版本号
$versionLine = Get-Content "main.py" | Select-String 'APP_VERSION = "(.+)"'
if ($versionLine -match 'APP_VERSION = "(.+)"') {
    $VERSION = $matches[1]
    Write-Host "检测到应用版本: $VERSION"
} else {
    $VERSION = "unknown"
    Write-Host "未检测到版本号，使用默认值: $VERSION"
}

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
    (Get-Content PolyAnalyzer.spec) -replace 'upx=True', 'upx=False' | Set-Content PolyAnalyzer.spec
} else {
    Write-Host "UPX 已安装"
}

# 5. 执行打包
Write-Host "步骤 5/6: 开始打包..."
pyinstaller PolyAnalyzer.spec --clean

# 6. 显示结果
Write-Host "步骤 6/6: 打包完成!"
if (Test-Path "dist\PolyAnalyzer.exe") {
    # 重命名为带版本号的文件
    $newName = "PolyAnalyzer_v$VERSION.exe"
    Rename-Item -Path "dist\PolyAnalyzer.exe" -NewName $newName
    
    Write-Host "================================"
    Write-Host "✅ 打包成功!"
    Write-Host "可执行文件: dist\$newName"
    $fileSize = (Get-Item "dist\$newName").Length / 1MB
    Write-Host "文件大小: $([math]::Round($fileSize, 2)) MB"
    Write-Host "================================"
    Write-Host "运行方法:"
    Write-Host "  cd dist"
    Write-Host "  .\$newName"
    Write-Host "================================"
} else {
    Write-Host "❌ 打包失败,请检查错误信息"
    exit 1
}
