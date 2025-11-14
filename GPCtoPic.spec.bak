# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec 文件 - 用于优化打包体积
执行: pyinstaller GPCtoPic.spec
"""

block_cipher = None

# 分析入口文件
a = Analysis(
    ['run_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('sinopec.jpg', '.'),  # 添加图片资源
        ('setting', 'setting'),  # 添加配置目录
    ],
    hiddenimports=[
        'streamlit',
        'numpy',
        'pandas',
        'matplotlib',
        'matplotlib.backends.backend_agg',  # 明确指定 Agg 后端
        'plottable',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 排除不需要的包以减少体积
    excludes=[
        'IPython',
        'jupyter',
        'notebook',
        'matplotlib.tests',
        'matplotlib.backends.backend_qt5agg',  # 排除 Qt 后端
        'matplotlib.backends.backend_tkagg',  # 排除 Tk 后端
        'matplotlib.backends.backend_wxagg',  # 排除 Wx 后端
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'sphinx',
        'pytest',
        'setuptools',
        'pip',
        'wheel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 过滤二进制文件,排除不需要的库
a.binaries = [x for x in a.binaries if not x[0].startswith('Qt')]
a.binaries = [x for x in a.binaries if not x[0].startswith('PySide')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GPCtoPic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # 启用符号剥离(macOS/Linux)
    upx=True,  # 启用 UPX 压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台窗口以显示 Streamlit 输出
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="main.ico",  # 可选: 添加应用图标路径
)
