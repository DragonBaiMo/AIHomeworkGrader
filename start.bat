@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo AI 作业批改工具 - 启动脚本
echo ========================================
echo.

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查虚拟环境是否存在
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在或不完整
    echo [提示] 请先运行 reset-env.bat 初始化环境
    pause
    exit /b 1
)

:: 检查核心依赖是否安装（检查 fastapi）
if not exist ".venv\Lib\site-packages\fastapi" (
    echo [错误] 项目依赖未安装或不完整
    echo [提示] 请先运行 reset-env.bat 初始化环境
    pause
    exit /b 1
)

:: 检查 uvicorn 是否安装
if not exist ".venv\Lib\site-packages\uvicorn" (
    echo [错误] uvicorn 未安装
    echo [提示] 请先运行 reset-env.bat 初始化环境
    pause
    exit /b 1
)

echo [启动] 正在启动 AI 作业批改工具...
echo.
echo 系统信息:
echo   - 框架: FastAPI + Uvicorn
echo   - 端口: 8000
echo   - 功能: 批量 docx 作业批改与导出
echo.
echo 访问地址:
echo   - 前端界面: http://localhost:8000
echo   - API 文档: http://localhost:8000/docs
echo   - 健康检查: http://localhost:8000/health
echo.
echo ========================================
echo.
echo [提示] 按 Ctrl+C 停止服务
echo.

:: 使用虚拟环境中的 Python 启动应用
"%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

:: 服务退出后的处理
echo.
echo ========================================
if %errorlevel% neq 0 (
    echo [错误] 服务异常退出，错误代码: %errorlevel%
) else (
    echo [信息] 服务已停止
)
echo ========================================
pause
