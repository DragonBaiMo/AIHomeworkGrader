# -*- mode: python ; coding: utf-8 -*-
"""
AI 作业批改工具 - PyInstaller 打包配置文件

使用方法：
    pyinstaller build_config.spec

说明：
    - 打包成单目录模式（onedir），启动速度更快
    - 包含所有必要的数据文件和静态资源
    - 自动包含前端构建产物
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 项目根目录
BACKEND_DIR = Path(SPECPATH)
PROJECT_ROOT = BACKEND_DIR.parent

# 收集所有子模块
hidden_imports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',
    'httptools',
    'websockets',
    'httpx',
    'httpcore',
    'anyio._backends._asyncio',
    'pydantic',
    'fastapi',
    'starlette',
    'docx',
    'openpyxl',
]

# 收集 pydantic 和 fastapi 的所有子模块
hidden_imports += collect_submodules('pydantic')
hidden_imports += collect_submodules('fastapi')
hidden_imports += collect_submodules('starlette')
hidden_imports += collect_submodules('docx')

# 数据文件：包含静态资源、配置文件、模板等
datas = [
    # 前端静态资源（构建后的产物）
    (str(BACKEND_DIR / 'app' / 'static'), 'app/static'),
    # 配置文件
    (str(BACKEND_DIR / 'config'), 'config'),
    # 数据目录结构（不包含上传的文件）
    # 运行时会自动创建 data 目录
]

# 检查静态资源目录是否存在
static_dir = BACKEND_DIR / 'app' / 'static'
if not static_dir.exists() or not any(static_dir.iterdir()):
    print("=" * 60)
    print("[警告] 前端静态资源目录为空或不存在！")
    print("请先运行前端构建命令:")
    print("  cd frontend && npm run build")
    print("=" * 60)

# 主分析配置
a = Analysis(
    ['app_launcher.py'],              # 入口脚本
    pathex=[str(BACKEND_DIR)],        # 搜索路径
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',                     # 排除不需要的模块
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],                                # 不打包所有文件到exe内部
    exclude_binaries=True,
    name='AI作业批改工具',              # 可执行文件名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                          # 使用 UPX 压缩
    console=True,                      # 显示控制台窗口（便于查看日志）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='app/static/favicon.ico',   # 如有图标可取消注释
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI作业批改工具',
)
