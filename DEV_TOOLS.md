# PolyAnalyzer 开发环境

PolyAnalyzer 使用 Tauri v2 + React + TypeScript + Python sidecar。

## 1. Node.js 与 pnpm

建议使用 Node.js 20 或更高版本、pnpm 9 或更高版本。

```bash
corepack enable
corepack prepare pnpm@9 --activate
pnpm install
```

前端命令：

```bash
pnpm dev
pnpm build
```

`pnpm dev` 只启动 Vite。日常联调应使用 `pnpm tauri dev`。

## 2. Rust 与 Tauri

安装 stable Rust：

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

另需安装当前平台的 [Tauri v2 系统依赖](https://v2.tauri.app/start/prerequisites/)。

Rust 验证命令：

```bash
cargo check --manifest-path src-tauri/Cargo.toml
cargo test --manifest-path src-tauri/Cargo.toml
```

## 3. Python sidecar

从项目根目录创建环境并安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install -r python/requirements.txt
python -m pip install pyinstaller
```

运行测试并构建当前平台的 sidecar：

```bash
python -m unittest discover -s python/tests -p "test_*.py"
python python/build_sidecar.py
```

不要手工改写 `src-tauri/binaries/` 中的产物；应始终由 `python/build_sidecar.py` 生成。

## 4. 桌面联调和打包

```bash
pnpm tauri dev
pnpm tauri build
```

`pnpm tauri build` 会先运行 `pnpm build`，并为当前平台生成 `bundle.targets = "all"` 支持的安装包。

## 5. 版本同步

```bash
./release.sh X.Y.Z
```

该命令只同步 package、Tauri、Cargo/Cargo.lock 和 Python 的版本字段。提交、tag 和 Release 仍由发布流程单独完成。

## 6. 缓存位置

| 内容 | 位置 |
|------|------|
| pnpm 依赖 | `node_modules/` 和 pnpm store |
| Rust 构建缓存 | `src-tauri/target/` |
| Python 虚拟环境 | `.venv/` |
| PyInstaller 缓存 | Python/PyInstaller 的平台缓存目录 |

需要清理时使用各工具自身命令，例如 `cargo clean --manifest-path src-tauri/Cargo.toml` 和 `pnpm store prune`。清理会增加下一次构建时间。
