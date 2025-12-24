#!/bin/bash

# AI 作业批改工具 - 启动脚本 (Mac/Linux)

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$BASE_DIR/backend"
APP_PORT=18088

echo "========================================"
echo "AI 作业批改工具 - 启动脚本"
echo "========================================"
echo

# 切换到项目根目录
cd "$BASE_DIR"

# 检查虚拟环境是否存在
if [[ ! -f "$BASE_DIR/.venv/bin/python" ]]; then
    echo "[错误] 虚拟环境不存在或不完整"
    echo "[提示] 请先运行 reset-env.sh 初始化环境"
    exit 1
fi

# 检查核心依赖是否安装（检查 fastapi）
if ! ls "$BASE_DIR/.venv/lib/"python*/site-packages/fastapi &>/dev/null; then
    echo "[错误] 项目依赖未安装或不完整"
    echo "[提示] 请先运行 reset-env.sh 初始化环境"
    exit 1
fi

# 检查 uvicorn 是否安装
if ! ls "$BASE_DIR/.venv/lib/"python*/site-packages/uvicorn &>/dev/null; then
    echo "[错误] uvicorn 未安装"
    echo "[提示] 请先运行 reset-env.sh 初始化环境"
    exit 1
fi

echo "[启动] 正在启动 AI 作业批改工具..."
echo
echo "系统信息:"
echo "  - 后端: FastAPI + Uvicorn"
echo "  - 前端: Vue3 (Vite 打包后静态托管)"
echo "  - 端口: $APP_PORT"
echo "  - 功能: 批量作业文件（docx/Markdown/txt）批改与导出"
echo
echo "访问地址:"
echo "  - 前端界面: http://localhost:$APP_PORT"
echo "  - 后端 OpenAPI: http://localhost:$APP_PORT/docs"
echo "  - 健康检查: http://localhost:$APP_PORT/health"
echo
echo "========================================"
echo
echo "[提示] 按 Ctrl+C 停止服务"
echo

# 切换到 backend 目录并启动后端服务
cd "$BACKEND_DIR"
export PYTHONPATH="$BACKEND_DIR"
"$BASE_DIR/.venv/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT"

# 服务退出后的处理
EXIT_CODE=$?
echo
echo "========================================"
if [[ $EXIT_CODE -ne 0 ]]; then
    echo "[错误] 服务异常退出，错误代码: $EXIT_CODE"
else
    echo "[信息] 服务已停止"
fi
echo "========================================"
