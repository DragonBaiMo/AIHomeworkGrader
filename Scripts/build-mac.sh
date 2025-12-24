#!/bin/bash

# ========================================
# AI 作业批改工具 - Mac/Linux 打包脚本
# ========================================
# 功能：一键打包成可执行文件
# 用法：./build-mac.sh
# ========================================

set -e  # 遇到错误立即退出

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$BASE_DIR/backend"
FRONTEND_DIR="$BASE_DIR/frontend"
DIST_DIR="$BACKEND_DIR/dist"
BUILD_DIR="$BACKEND_DIR/build"

echo "========================================"
echo "AI 作业批改工具 - Mac/Linux 打包脚本"
echo "========================================"
echo

# 切换到项目根目录
cd "$BASE_DIR"

# ========================================
# 步骤 1：检查 Python 环境
# ========================================
echo "[步骤 1/5] 检查 Python 环境..."

# 优先使用虚拟环境
if [[ -f "$BASE_DIR/.venv/bin/python" ]]; then
    PYTHON="$BASE_DIR/.venv/bin/python"
    PIP="$BASE_DIR/.venv/bin/pip"
    echo "  使用虚拟环境 Python"
else
    if ! command -v python3 &> /dev/null; then
        echo "[错误] 未找到 Python 环境"
        echo "[提示] 请先安装 Python 3.9+ 或运行 reset-env.sh 创建虚拟环境"
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
echo "[步骤 2/5] 检查打包依赖..."

if ! "$PYTHON" -c "import PyInstaller" 2>/dev/null; then
    echo "  正在安装 PyInstaller..."
    "$PIP" install pyinstaller -q
fi
echo "  PyInstaller 已就绪"

# 确保后端依赖已安装
"$PIP" install -q -r "$BACKEND_DIR/requirements.txt"

# ========================================
# 步骤 3：构建前端
# ========================================
echo
echo "[步骤 3/5] 构建前端..."

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "[错误] 未找到 Node.js"
    echo "[提示] 请先安装 Node.js 16+"
    exit 1
fi

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "[错误] 未找到 npm"
    exit 1
fi

# 切换到前端目录
cd "$FRONTEND_DIR"

# 安装依赖（如果需要）
if [[ ! -d "node_modules" ]]; then
    echo "  安装前端依赖..."
    npm install
fi

# 构建前端
echo "  执行前端构建..."
npm run build
echo "  前端构建完成"

# ========================================
# 步骤 4：打包后端
# ========================================
echo
echo "[步骤 4/5] 打包后端..."

cd "$BACKEND_DIR"

# 清理旧的构建产物
if [[ -d "$DIST_DIR" ]]; then
    echo "  清理旧的打包文件..."
    rm -rf "$DIST_DIR"
fi
if [[ -d "$BUILD_DIR" ]]; then
    rm -rf "$BUILD_DIR"
fi

# 执行 PyInstaller 打包
echo "  开始打包（这可能需要几分钟）..."
"$PYTHON" -m PyInstaller build_config.spec --noconfirm

# ========================================
# 步骤 5：创建运行时数据目录
# ========================================
echo
echo "[步骤 5/5] 整理打包产物..."

OUTPUT_DIR="$DIST_DIR/AI作业批改工具"
if [[ -d "$OUTPUT_DIR" ]]; then
    # 创建运行时目录
    mkdir -p "$OUTPUT_DIR/data/uploads"
    echo "  创建运行时目录完成"
    
    # 设置可执行权限
    chmod +x "$OUTPUT_DIR/AI作业批改工具"
    echo "  设置执行权限完成"
    
    # 创建启动脚本
    cat > "$OUTPUT_DIR/启动.command" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./AI作业批改工具
EOF
    chmod +x "$OUTPUT_DIR/启动.command"
    echo "  创建启动脚本完成"
fi

# ========================================
# 完成
# ========================================
echo
echo "========================================"
echo "[成功] 打包完成！"
echo "========================================"
echo
echo "打包产物位置: $OUTPUT_DIR"
echo
echo "使用方法:"
echo "  1. 将整个文件夹复制到目标机器"
echo "  2. 双击 '启动.command' 或在终端运行 './AI作业批改工具'"
echo "  3. 浏览器会自动打开访问界面"
echo
echo "注意事项:"
echo "  - 确保目标机器有网络连接（用于调用 AI API）"
echo "  - 首次运行时会自动创建数据目录"
echo "  - 关闭终端窗口即可停止服务"
echo
echo "如需创建 Mac 应用程序包(.app)，请使用:"
echo "  ./build-mac-app.sh"
echo
