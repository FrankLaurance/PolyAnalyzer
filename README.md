# PolyAnalyzer 2.4.0

[English](README_EN.md)

PolyAnalyzer 是一个基于 Tauri v2、React 和 Python sidecar 的桌面分析工具，用于处理高分子表征数据。

## 功能

| 模块 | 输入 | 主要输出 |
|------|------|----------|
| GPC | `.rst` / `.xls` / `.xlsx` | 分子量汇总、色谱图和峰数据 |
| Mw | `.rst` / `.xls` / `.xlsx` | 分子量分布图和区间统计 |
| DSC | `.txt` | 分段数据、分段曲线和循环对比图 |
| IR | `.dpt` | 红色单谱图、可选峰归一化叠加图和 manifest |

v2.4.0 亮点：

- GPC/Mw 支持仪器 Excel 导出（`.xls`/`.xlsx`），自动识别 `LogM`/`MMD`/`Cumulative` 列组与 Results 汇总表，任意样品数均可；单位与 `.rst` 版本一致
- 引擎预热横幅：打开应用后后台预热绘图引擎，预热期间全局提示、完成后自动消失
- 内置中英双语"使用说明"窗口（帮助区打开，含目录跳转）

前端通过 stdin/stdout JSON-RPC 调用 Python sidecar。分析进度包含 analyzer 和 request ID，避免多个标签页之间互相覆盖。

## 快速启动

### 环境要求

- Node.js 20+
- pnpm 9+
- Rust stable 工具链
- Python 3.11+
- 当前平台所需的 [Tauri v2 系统依赖](https://v2.tauri.app/start/prerequisites/)

### 从源码运行

```bash
git clone https://github.com/FrankLaurance/PolyAnalyzer.git
cd PolyAnalyzer

python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install -r python/requirements.txt
python -m pip install -r python/requirements-build.txt
pnpm install

python python/build_sidecar.py
pnpm tauri dev
```

`python/build_sidecar.py` 会为当前平台生成 Tauri 所需的 `polyanalyzer-engine` 和 `poly` sidecar。sidecar 生成后再启动或打包应用。

## 验证

```bash
python -m unittest discover -s python/tests -p "test_*.py"
pnpm test
pnpm build
python python/build_sidecar.py
cargo check --manifest-path src-tauri/Cargo.toml
cargo test --manifest-path src-tauri/Cargo.toml
```

## 打包

```bash
python python/build_sidecar.py
pnpm tauri build
```

`bundle.targets` 使用 `all`，会生成当前平台支持的安装包：Windows 的 MSI/NSIS、Linux 的 deb/AppImage，以及 macOS 的 app/dmg。

## 版本同步

```bash
./release.sh 2.4.0
```

脚本只同步版本字段，不创建 commit、Git tag 或 GitHub Release。它会更新：

- `package.json`
- `src-tauri/tauri.conf.json`
- `src-tauri/Cargo.toml`
- `src-tauri/Cargo.lock`
- `python/analyzer/base.py`

GitHub Actions 在 tag 构建时会从 `vX.Y.Z` 提取 `X.Y.Z` 并先运行该脚本。

## 命令行

源码环境可直接使用 Python CLI：

```bash
python python/cli.py --help
```

CLI 覆盖 GPC、Mw、DSC 和 IR；完整参数见 [CLI_USAGE.md](CLI_USAGE.md) 和 [CLI_USAGE_EN.md](CLI_USAGE_EN.md)。

桌面界面与 CLI 共用 `setting/profiles/{mw,dsc,ir}/` 下的 Analysis Profile。旧版默认配置会自动迁移；桌面端保留 localStorage 缓存，并在 sidecar 连接后双向同步命名配置。

## 输出位置

- GPC：所选数据目录同级的 `GPC_output/`
- Mw：所选数据目录同级的 `Mw_output/`
- DSC：所选数据目录同级的 `DSC_Cycle/` 和 `DSC_Pic/`
- IR：应用可写数据根目录下的 `IR_output/`

开发环境的默认可写数据根目录是项目目录；安装包运行时使用操作系统的 PolyAnalyzer 用户数据目录。

## 项目结构

```text
src/                    React 前端
src-tauri/              Tauri/Rust 应用和能力配置
python/                 JSON-RPC sidecar、分析器和 CLI
python/tests/           Python unittest
.github/workflows/      多平台构建与发布
release.sh              版本同步脚本
```

用户操作说明见应用内"使用说明"窗口（源文件 [public/manual.html](public/manual.html)），开发依赖说明见 [DEV_TOOLS.md](DEV_TOOLS.md)。

## License

[MIT](LICENSE)
