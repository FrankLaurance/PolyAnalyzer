# GPCtoPic PyInstaller 打包指南

## 📦 优化说明

本项目已针对 PyInstaller 打包进行了优化,可将 exe 文件体积从 ~300-500MB 减小到 ~100-200MB。

### 优化措施

1. **延迟导入**: matplotlib 和 plottable 改为在需要时才导入
2. **排除不需要的包**: 通过 spec 文件排除 Qt、Tk、Jupyter 等大型依赖
3. **使用 Agg 后端**: matplotlib 使用非交互式后端,减少依赖
4. **UPX 压缩**: 启用 UPX 对可执行文件进行压缩
5. **符号剥离**: 移除调试符号以减小体积

## 🚀 快速开始

### 方法 1: 使用自动化脚本(推荐)

#### macOS/Linux:
```bash
./build.sh
```

#### Windows:
```powershell
.\build.ps1
```

### 方法 2: 手动打包

1. **安装 PyInstaller**:
```bash
pip install pyinstaller
```

2. **可选 - 安装 UPX 压缩工具**:

   **macOS**: 
   ```bash
   brew install upx
   ```

   **Linux**: 
   ```bash
   sudo apt-get install upx
   # 或
   sudo yum install upx
   ```

   **Windows**: 
   - 从 https://upx.github.io/ 下载
   - 解压后将 upx.exe 添加到 PATH 环境变量

3. **执行打包**:
```bash
pyinstaller GPCtoPic.spec --clean
```

4. **查看结果**:
- 可执行文件位于 `dist/` 目录
- macOS/Linux: `dist/GPCtoPic`
- Windows: `dist\GPCtoPic.exe`

## 📝 配置文件说明

### GPCtoPic.spec
PyInstaller 配置文件,包含:
- 入口文件: `run_main.py`
- 数据文件: `sinopec.jpg`, `setting/` 目录
- 排除包列表: Qt、Tk、Jupyter 等
- 压缩选项: UPX、符号剥离

### requirements.txt
最小化依赖列表,仅包含必需的包:
- streamlit
- numpy
- pandas
- matplotlib
- plottable
- openpyxl

## 🔧 打包参数说明

### 体积优化相关:
- `excludes`: 排除不需要的大型包
- `strip=True`: 剥离调试符号(macOS/Linux)
- `upx=True`: 启用 UPX 压缩
- `console=True`: 保留控制台窗口(显示 Streamlit 日志)

### 自定义图标(可选):
编辑 `GPCtoPic.spec` 中的 `icon` 参数:
```python
icon='path/to/your/icon.ico',  # Windows
# 或
icon='path/to/your/icon.icns',  # macOS
```

## 📊 预期体积

| 配置 | 大小 |
|-----|------|
| 未优化 | ~300-500MB |
| 基础优化(排除包) | ~200-250MB |
| 完全优化(排除包+UPX) | ~100-200MB |

*实际大小取决于具体环境和依赖版本*

## 🐛 常见问题

### 1. 导入错误
**问题**: 打包后运行提示 "No module named xxx"

**解决**: 在 `GPCtoPic.spec` 的 `hiddenimports` 列表中添加缺失的模块

### 2. 文件未找到
**问题**: 打包后找不到 `sinopec.jpg` 或配置文件

**解决**: 检查 `GPCtoPic.spec` 中的 `datas` 列表是否正确

### 3. UPX 警告
**问题**: "UPX is not available"

**解决**: 
- 安装 UPX 或
- 在 spec 文件中设置 `upx=False`

### 4. 体积仍然很大
**解决步骤**:
1. 确认已排除不需要的包
2. 确认已启用 UPX 压缩
3. 检查是否有其他大型依赖被意外包含
4. 使用 `pyinstaller --analyze` 分析依赖

## 🧪 测试打包结果

```bash
# macOS/Linux
cd dist
./GPCtoPic

# Windows
cd dist
.\GPCtoPic.exe
```

程序应该会启动并打开浏览器显示 Streamlit 界面。

## 📝 注意事项

1. **首次运行较慢**: 打包后的程序首次运行需要解压,会比较慢
2. **防病毒软件**: 某些防病毒软件可能会误报,需要添加信任
3. **路径问题**: 确保不使用中文路径
4. **环境一致性**: 在目标系统相似的环境中打包可获得最佳兼容性

## 🔄 更新打包

修改代码后重新打包:
```bash
# 清理旧文件
rm -rf build dist

# 重新打包
./build.sh  # 或 pyinstaller GPCtoPic.spec --clean
```

## 📚 相关资源

- [PyInstaller 官方文档](https://pyinstaller.org/)
- [UPX 压缩工具](https://upx.github.io/)
- [Streamlit 文档](https://docs.streamlit.io/)
