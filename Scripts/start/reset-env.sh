#!/bin/bash

# AI 作业批改工具 - 虚拟环境重置脚本 (Mac/Linux)

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$BASE_DIR/backend"

echo "========================================"
echo "AI 作业批改工具 - 虚拟环境重置脚本"
echo "========================================"
echo

# 切换到项目根目录
cd "$BASE_DIR"

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3,请先安装 Python 3.8+"
    exit 1
fi

echo "[提示] 检测到 Python 环境正常"
python3 --version
echo

# 询问用户是否继续
read -p "是否继续重置虚拟环境? 这将删除现有的所有依赖 (Y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "[取消] 用户取消操作"
    exit 0
fi

echo
echo "========================================"
echo "第一步: 清理现有虚拟环境"
echo "========================================"
echo

# 检查 requirements.txt 是否存在
if [[ ! -f "$BACKEND_DIR/requirements.txt" ]]; then
    echo "[错误] 未找到 backend/requirements.txt,请确保在正确的项目目录"
    exit 1
fi

# 删除虚拟环境
if [[ -d ".venv" ]]; then
    echo "[清理] 正在删除虚拟环境 .venv..."
    rm -rf ".venv"
    echo "[完成] 虚拟环境已删除"
else
    echo "[跳过] .venv 虚拟环境不存在"
fi

# 删除 Python 缓存
echo "[清理] 正在删除 Python 缓存..."
find "$BACKEND_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find "$BACKEND_DIR" -type f -name "*.pyc" -delete 2>/dev/null
echo "[完成] __pycache__ 缓存已清理"

# 删除 pytest 缓存
if [[ -d "$BACKEND_DIR/.pytest_cache" ]]; then
    echo "[清理] 正在删除 pytest 缓存..."
    rm -rf "$BACKEND_DIR/.pytest_cache"
    echo "[完成] pytest 缓存已清理"
fi

echo
echo "========================================"
echo "第二步: 创建虚拟环境"
echo "========================================"
echo

echo "[创建] 正在创建 Python 虚拟环境..."
python3 -m venv .venv
if [[ $? -ne 0 ]]; then
    echo "[错误] 创建虚拟环境失败"
    exit 1
fi
echo "[完成] Python 虚拟环境创建成功"

echo
echo "========================================"
echo "第三步: 升级 pip 并安装依赖"
echo "========================================"
echo

echo "[升级] 正在升级 pip..."
.venv/bin/python -m pip install --upgrade pip
if [[ $? -ne 0 ]]; then
    echo "[警告] pip 升级失败,但将继续安装依赖"
fi

echo "[安装] 正在安装后端依赖..."
.venv/bin/pip install -r "$BACKEND_DIR/requirements.txt"
if [[ $? -ne 0 ]]; then
    echo "[错误] 依赖安装失败"
    exit 1
fi
echo "[完成] 项目依赖安装成功"

echo
echo "========================================"
echo "重置完成!"
echo "========================================"
echo
echo "[成功] 虚拟环境已重置完成,可以开始使用"
echo
echo "后续操作:"
echo "  1. 运行 ./Scripts/start.sh 启动后端（内置静态资源，端口 18088）"
echo "  2. 手动启动后端:"
echo "     cd backend && ../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 18088"
echo "  3. 前端开发模式:"
echo "     cd frontend && npm install && npm run dev -- --host"
echo
echo "访问地址:"
echo "  - 前端界面: http://localhost:18088"
echo "  - 后端 OpenAPI: http://localhost:18088/docs"
echo "  - 健康检查: http://localhost:18088/health"
echo
