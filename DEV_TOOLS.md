# 开发工具安装与卸载指南

本项目使用 Tauri v2 + React + Python 架构，以下是所有开发依赖的安装/卸载方式及磁盘占用。

---

## 1. Rust 工具链 (~1.2 GB)

通过 `rustup` 管理，包含 `cargo`、`rustc`、`rustfmt` 等。

```bash
# 安装
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

# 卸载（会删除 ~/.rustup 和 ~/.cargo）
rustup self uninstall
```

**磁盘位置：**
- `~/.rustup/` — Rust 工具链 (~1.2 GB)
- `~/.cargo/` — Cargo 包管理器、缓存 (~183 MB)

---

## 2. pnpm 包管理器 (~258 MB store)

```bash
# 安装
npm install -g pnpm

# 卸载
npm uninstall -g pnpm
rm -rf ~/Library/pnpm          # macOS
rm -rf ~/.local/share/pnpm     # Linux
```

**磁盘位置：**
- 全局二进制：`$(npm root -g)/pnpm`
- 包存储：`~/Library/pnpm/store/` (macOS) 或 `~/.local/share/pnpm/store/` (Linux) (~258 MB)

---

## 3. Node.js 依赖 (~285 MB)

项目本地的前端依赖。

```bash
# 安装
pnpm install

# 卸载（删除项目内 node_modules）
rm -rf node_modules
```

**磁盘位置：**
- `<项目>/node_modules/` (~285 MB)

---

## 4. Rust 编译缓存 (~2.6 GB debug)

Tauri 编译产物，首次构建较大，后续增量编译很快。

```bash
# 清理编译缓存
cd src-tauri && cargo clean

# 或直接删除
rm -rf src-tauri/target
```

**磁盘位置：**
- `<项目>/src-tauri/target/` (~2.6 GB debug 模式)

---

## 5. Python 依赖

项目后端使用 Python + numpy/scipy/pandas/matplotlib。

```bash
# 安装（建议使用虚拟环境）
cd python
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows
pip install numpy scipy pandas matplotlib

# 卸载
deactivate
rm -rf python/venv
```

---

## 一键清理所有开发缓存

保留工具链，只清理项目缓存：

```bash
rm -rf node_modules
cd src-tauri && cargo clean && cd ..
rm -rf python/venv
```

## 完全卸载所有工具

```bash
# 1. 清理项目
rm -rf node_modules
rm -rf src-tauri/target
rm -rf python/venv

# 2. 卸载 Rust
rustup self uninstall

# 3. 卸载 pnpm
npm uninstall -g pnpm
rm -rf ~/Library/pnpm          # macOS
rm -rf ~/.local/share/pnpm     # Linux

# 4. 清理 pnpm 全局存储
pnpm store prune               # 在卸载前运行，清理未引用的包
```

---

## 磁盘占用汇总

| 组件 | 位置 | 大小 |
|------|------|------|
| Rust 工具链 | `~/.rustup/` | ~1.2 GB |
| Cargo 缓存 | `~/.cargo/` | ~183 MB |
| pnpm 存储 | `~/Library/pnpm/store/` | ~258 MB |
| node_modules | `<项目>/node_modules/` | ~285 MB |
| Rust 编译缓存 | `<项目>/src-tauri/target/` | ~2.6 GB (debug) |
| **合计** | | **~4.5 GB** |
