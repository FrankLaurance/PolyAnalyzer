# PolyAnalyzer CLI 使用说明

`poly` 是 PolyAnalyzer 的批处理命令行工具，适合把 GPC、Mw、DSC 和 IR 分析接入脚本、批量任务或自动化流程。CLI 只生成文件和命令行结果，不打开桌面界面，也不预览图片。

原则：桌面界面中有批处理意义的设置，都应有对应 CLI 参数。保存到 `setting/` 的 Mw/DSC/IR Analysis Profile 可以通过 `--setting` 载入；命令行显式传入的参数优先级高于配置文件。

## 安装与调用

### 源码环境

```bash
cd PolyAnalyzer
pip install -r python/requirements.txt
python3 python/cli.py --help
```

源码环境中，所有示例都可以把 `poly` 替换为：

```bash
python3 python/cli.py
```

### 安装包环境

CLI 随 Tauri 桌面安装包分发，但不会注册到全局 `PATH`。请从安装目录或应用资源目录调用：

| 平台 | 典型路径 |
|------|----------|
| Windows | `C:\Program Files\PolyAnalyzer\poly.exe` 或用户安装目录下的 `poly.exe` |
| macOS | `/Applications/PolyAnalyzer.app/Contents/MacOS/poly` |
| Linux deb | `/usr/lib/polyanalyzer/poly` 或安装包资源目录下的 `poly` |
| Linux AppImage | 解包后的 `squashfs-root/usr/lib/polyanalyzer/poly`，或 AppImage 运行目录内的资源路径 |

macOS 示例：

```bash
"/Applications/PolyAnalyzer.app/Contents/MacOS/poly" --help
```

## 通用输出选项

每个业务子命令都支持：

```bash
--json    # stdout 输出机器可读 JSON，进度写入 stderr
--quiet   # 不输出进度
```

退出码：

| 退出码 | 含义 |
|--------|------|
| `0` | 成功 |
| `1` | 分析失败或输出已存在 |
| `2` | 参数错误 |

## GPC 分析

输入目录必须包含 `.rst` 文件。默认输出到数据目录同级的 `GPC_output/`。

```bash
poly gpc --datadir ./datapath --output-name 20260328
```

常用选项：

```bash
poly gpc \
  --datadir ./datapath \
  --output-name batch-001 \
  --file HR-D901B.rst UH-D901D.rst \
  --overwrite
```

可选参数：

| 参数 | 说明 |
|------|------|
| `--file NAME ...` | 只处理指定 `.rst` 文件，可重复 |
| `--overwrite` | 允许覆盖同名输出 |
| `--no-csv` | 不输出分子量汇总 CSV |
| `--no-image` | 不输出 PNG 图片 |
| `--no-xlsx` | 不输出峰数据 XLSX |

输出文件：

- `GPC_output/{output-name}.csv`
- `GPC_output/{output-name}.png`
- `GPC_output/{output-name}.xlsx`

## Mw 分析

输入目录必须包含 `.rst` 文件。默认输出到数据目录同级的 `Mw_output/`。

```bash
poly mw --datadir ./datapath
```

指定文件、分子量分段和样式：

```bash
poly mw \
  --datadir ./datapath \
  --file HR-D901B.rst \
  --segments 0,5000,10000,50000,100000,500000,1000000 \
  --bar-color '#002FA7' \
  --mw-color '#FF6A07' \
  --line-width 1.2
```

按连续范围定义分隔区间：

```bash
poly mw \
  --datadir ./datapath \
  --ranges 0-5000,5000-10000,10000-50000,50000-100000
```

从设置文件读取默认值，再用命令行覆盖部分参数：

```bash
poly mw \
  --datadir ./datapath \
  --setting publication.json \
  --ranges 0-10000,10000-50000,50000-500000 \
  --no-table
```

常用绘图参数：

| 参数 | 说明 |
|------|------|
| `--setting NAME` | 载入 `setting/` 中的 Mw 设置文件，命令行参数会覆盖它 |
| `--segments 0,5000,...` | 分子量区间分割点，必须递增 |
| `--ranges 0-5000,5000-10000` | 按连续范围定义区间，等价于分隔点 `0,5000,10000` |
| `--no-image` | 不输出 PNG 图片 |
| `--draw-bar` / `--no-bar` | 是否绘制柱状图 |
| `--draw-mw-curve` / `--no-mw-curve` | 是否绘制 Mw 曲线 |
| `--draw-table` / `--no-table` | 是否绘制数据表格 |
| `--bar-color COLOR` | 柱状图颜色 |
| `--mw-color COLOR` | Mw 曲线颜色 |
| `--bar-width N` | 柱状图宽度系数 |
| `--line-width N` | 曲线线宽 |
| `--axis-width N` | 坐标轴线宽 |
| `--title-font-size N` | 标题字号 |
| `--axis-font-size N` | 坐标轴字号 |
| `--transparent-background` | 透明背景，默认 |
| `--opaque-background` | 不透明背景 |

输出文件：

- `Mw_output/{样品名}.png`

## DSC 分析

输入目录必须包含 `.txt` 文件。默认输出到数据目录同级的 `DSC_Cycle/` 和 `DSC_Pic/`。

```bash
poly dsc --datadir ./datapath
```

峰位方向和居中：

```bash
poly dsc \
  --datadir ./datapath \
  --setting defaultDSCSetting.ini \
  --peaks-upward \
  --center-peak \
  --left-length 1.9 \
  --right-length 1.9
```

常用参数：

| 参数 | 说明 |
|------|------|
| `--setting NAME` | 载入 `setting/` 中的 DSC 设置文件，命令行参数会覆盖它 |
| `--peaks-upward` | 将峰方向统一为向上 |
| `--center-peak` | 按检测到的峰居中显示 |
| `--left-length N` | 每段左侧裁剪长度 |
| `--right-length N` | 每段右侧裁剪长度 |
| `--no-segment-data` | 不保存分段 CSV |
| `--no-segment-plots` | 不绘制单循环图片 |
| `--no-cycle` | 不绘制循环叠加图 |
| `--no-cycle-image` | 不保存循环叠加图 |
| `--curve-color COLOR` | 曲线颜色 |
| `--line-width N` | 曲线线宽 |
| `--axis-width N` | 坐标轴线宽 |
| `--title-font-size N` | 标题字号 |
| `--axis-font-size N` | 坐标轴字号 |

输出文件：

- `DSC_Cycle/Cycle*/{样品名}.csv`
- `DSC_Cycle/Cycle*/result.png`
- `DSC_Pic/{样品名}/Cycle *.png`

## IR 分析

输入目录必须包含 `.dpt` 文件。输出位于 PolyAnalyzer 可写数据根目录的 `IR_output/`。

```bash
poly ir --datadir ../IR
```

指定文件、配置和峰归一化位置：

```bash
poly ir \
  --datadir ../IR \
  --file 26-17.dpt 26-9.dpt \
  --setting defaultIRSetting.ini \
  --normalization-peak 1450 \
  --curve-color '#D62728'
```

常用参数：

| 参数 | 说明 |
|------|------|
| `--file NAME ...` | 只处理指定 `.dpt` 文件，可重复 |
| `--setting NAME` | 载入 IR Analysis Profile |
| `--overlay` / `--no-overlay` | 是否生成叠加图 |
| `--normalize-overlay` / `--no-normalize-overlay` | 是否对叠加图进行峰归一化 |
| `--normalization-peak N` | 归一化峰位，范围 400–4000 cm⁻¹ |
| `--curve-color COLOR` | 单谱图和首条叠加曲线颜色 |

输出文件：

- `IR_output/individual/{样品名}.png`
- `IR_output/dpt_overlay.png`（启用叠加图时）
- `IR_output/manifest.json`

## 清理输出目录

`clean` 只清理数据目录同级的 `Mw_output/`、`GPC_output/`、`DSC_Cycle/`、`DSC_Pic/`，以及应用可写数据根目录的 `IR_output/`。必须显式传入 `--yes`。

```bash
poly clean --datadir ./datapath --yes
```

## 设置管理

Analysis Profile 按类型保存在安装目录或源码目录下的 `setting/profiles/{mw,dsc,ir}/`。

```bash
poly settings list --type mw
poly settings show --type mw --name defaultSetting.ini
poly settings show --type dsc --name defaultDSCSetting.ini --json
poly settings show --type ir --name defaultIRSetting.ini --json
```

保存设置：

```bash
poly settings save \
  --type mw \
  --name publication.json \
  --set bar_color='"#002FA7"' \
  --set line_width=1.2 \
  --set draw_table=true
```

从 JSON 文件保存：

```bash
poly settings save --type dsc --name dsc-blue.json --from-json ./dsc-blue.json
```

删除设置：

```bash
poly settings delete --type mw --name publication.json
```

## JSON 输出示例

```bash
poly mw --datadir ./datapath --file HR-D901B.rst --json --quiet
```

输出：

```json
{
  "success": true,
  "message": "Mw analysis complete",
  "output_dir": "/path/to/Mw_output",
  "files": ["HR-D901B.rst"]
}
```

## 常见问题

**为什么安装后不能直接输入 `poly`？**  
本版本不注册全局 `PATH`，需要使用安装目录中的完整路径调用。

**输出已存在怎么办？**  
GPC 使用 `--overwrite` 覆盖同名输出。Mw 和 DSC 会按样品名覆盖同名图片或 CSV。

**CLI 会打开图形界面吗？**  
不会。CLI 只处理数据、生成文件并输出路径。
