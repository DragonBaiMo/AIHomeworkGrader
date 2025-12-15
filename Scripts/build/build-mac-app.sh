#!/bin/bash

# ========================================
# AI 作业批改工具 - Mac 应用程序包(.app)打包脚本
# ========================================
# 功能：打包成 macOS 标准应用程序
# 用法：./build-mac-app.sh
# ========================================

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$BASE_DIR/backend"
FRONTEND_DIR="$BASE_DIR/frontend"
DIST_DIR="$BACKEND_DIR/dist"
BUILD_DIR="$BACKEND_DIR/build"
APP_NAME="AI作业批改工具"

echo "========================================"
echo "AI 作业批改工具 - Mac 应用程序包打包脚本"
echo "========================================"
echo

# 切换到项目根目录
cd "$BASE_DIR"

# ========================================
# 步骤 1：检查环境
# ========================================
echo "[步骤 1/6] 检查环境..."

# 检查是否在 Mac 上运行
if [[ "$(uname)" != "Darwin" ]]; then
    echo "[错误] 此脚本仅支持 macOS 系统"
    exit 1
fi

# 检查 Python 环境
if [[ -f "$BASE_DIR/.venv/bin/python" ]]; then
    PYTHON="$BASE_DIR/.venv/bin/python"
    PIP="$BASE_DIR/.venv/bin/pip"
    echo "  使用虚拟环境 Python"
else
    if ! command -v python3 &> /dev/null; then
        echo "[错误] 未找到 Python 环境"
        echo "[提示] 请先运行 reset-env.sh 创建虚拟环境"
        exit 1
    fi
    PYTHON="python3"
    PIP="pip3"
    echo "  使用系统 Python"
fi

# 检查 Python 版本
if ! "$PYTHON" -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    echo "[错误] Python 版本过低，需要 3.9+"
    exit 1
fi
echo "  Python 环境检查通过"

# ========================================
# 步骤 2：安装打包依赖
# ========================================
echo
echo "[步骤 2/6] 检查打包依赖..."

if ! "$PYTHON" -c "import PyInstaller" 2>/dev/null; then
    echo "  正在安装 PyInstaller..."
    "$PIP" install pyinstaller -q
fi
echo "  PyInstaller 已就绪"

"$PIP" install -q -r "$BACKEND_DIR/requirements.txt"

# ========================================
# 步骤 3：构建前端
# ========================================
echo
echo "[步骤 3/6] 构建前端..."

if ! command -v node &> /dev/null; then
    echo "[错误] 未找到 Node.js，请先安装"
    exit 1
fi

cd "$FRONTEND_DIR"

if [[ ! -d "node_modules" ]]; then
    echo "  安装前端依赖..."
    npm install
fi

echo "  执行前端构建..."
npm run build
echo "  前端构建完成"

# ========================================
# 步骤 4：创建 Mac App 专用 spec 文件
# ========================================
echo
echo "[步骤 4/6] 生成 Mac App 配置..."

cd "$BACKEND_DIR"

# 创建临时的 Mac App spec 文件
cat > build_mac_app.spec << 'SPEC_EOF'
# -*- mode: python ; coding: utf-8 -*-
"""
AI 作业批改工具 - macOS 应用程序打包配置
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

BACKEND_DIR = Path(SPECPATH)
PROJECT_ROOT = BACKEND_DIR.parent

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

hidden_imports += collect_submodules('pydantic')
hidden_imports += collect_submodules('fastapi')
hidden_imports += collect_submodules('starlette')
hidden_imports += collect_submodules('docx')

datas = [
    (str(BACKEND_DIR / 'app' / 'static'), 'app/static'),
    (str(BACKEND_DIR / 'config'), 'config'),
]

a = Analysis(
    ['app_launcher.py'],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'cv2'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI作业批改工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                     # macOS App 不显示终端
    disable_windowed_traceback=False,
    argv_emulation=True,               # macOS App 需要此选项
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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

app = BUNDLE(
    coll,
    name='AI作业批改工具.app',
    icon=None,                         # 可以添加 .icns 图标文件
    bundle_identifier='com.aihomework.grader',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleName': 'AI作业批改工具',
        'CFBundleDisplayName': 'AI作业批改工具',
        'LSMinimumSystemVersion': '10.14.0',
        'NSAppleScriptEnabled': False,
    },
)
SPEC_EOF

echo "  Mac App 配置文件已生成"

# ========================================
# 步骤 5：执行打包
# ========================================
echo
echo "[步骤 5/6] 打包 Mac 应用程序..."

# 清理旧的构建产物
rm -rf "$DIST_DIR" "$BUILD_DIR" 2>/dev/null || true

echo "  开始打包（这可能需要几分钟）..."
"$PYTHON" -m PyInstaller build_mac_app.spec --noconfirm

# ========================================
# 步骤 6：后处理
# ========================================
echo
echo "[步骤 6/6] 整理打包产物..."

APP_PATH="$DIST_DIR/$APP_NAME.app"

if [[ -d "$APP_PATH" ]]; then
    # 创建运行时数据目录
    mkdir -p "$APP_PATH/Contents/MacOS/data/uploads"
    echo "  创建运行时目录完成"
    
    # 清理临时 spec 文件
    rm -f build_mac_app.spec
    
    echo
    echo "========================================"
    echo "[成功] Mac 应用程序打包完成！"
    echo "========================================"
    echo
    echo "应用程序位置: $APP_PATH"
    echo
    echo "使用方法:"
    echo "  1. 将 '$APP_NAME.app' 复制到应用程序文件夹"
    echo "  2. 双击应用程序图标启动"
    echo "  3. 浏览器会自动打开访问界面"
    echo
    echo "首次运行提示:"
    echo "  如果系统提示'无法验证开发者'，请按住 Ctrl 键点击应用程序，"
    echo "  然后选择'打开'，在弹出的对话框中再次点击'打开'。"
    echo
    echo "查看日志:"
    echo "  打开终端，运行: $APP_PATH/Contents/MacOS/AI作业批改工具"
    echo
    
    # 询问是否打开目录
    echo "是否打开打包目录？(y/n)"
    read -r answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        open "$DIST_DIR"
    fi
else
    echo "[错误] 打包失败，未找到输出文件"
    exit 1
fi
