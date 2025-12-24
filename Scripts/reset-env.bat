@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "BASE_DIR=%%~fI"
set "BACKEND_DIR=%BASE_DIR%\backend"
set "REQ_FILE=%BACKEND_DIR%\requirements.txt"

echo ========================================
echo AI 作业批改工具 - 虚拟环境重置脚本
echo ========================================
echo.

cd /d "%BASE_DIR%"

python --version >nul 2>&1
if errorlevel 1 goto :no_python

echo [提示] 检测到 Python 环境正常
echo.

set /p confirm="是否继续重置虚拟环境? 这将删除现有的所有依赖 (Y/N): "
if /i not "%confirm%"=="Y" goto :cancelled

echo.
echo ========================================
echo 第一步: 清理现有虚拟环境
echo ========================================
echo.

if not exist "%REQ_FILE%" goto :missing_requirements

if exist ".venv" (
    echo [清理] 正在删除虚拟环境 .venv...
    rmdir /s /q ".venv"
    echo [完成] 虚拟环境已删除
) else (
    echo [跳过] .venv 虚拟环境不存在
)

echo [清理] 正在删除 Python 缓存...
for /d /r "%BACKEND_DIR%" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo [完成] __pycache__ 缓存已清理

if exist "%BACKEND_DIR%\.pytest_cache" (
    echo [清理] 正在删除 pytest 缓存...
    rmdir /s /q "%BACKEND_DIR%\.pytest_cache"
    echo [完成] pytest 缓存已清理
)

echo.
echo ========================================
echo 第二步: 创建虚拟环境
echo ========================================
echo.

echo [创建] 正在创建 Python 虚拟环境...
python -m venv .venv
if errorlevel 1 goto :venv_failed
echo [完成] Python 虚拟环境创建成功

echo.
echo ========================================
echo 第三步: 升级 pip 并安装依赖
echo ========================================
echo.

echo [升级] 正在升级 pip...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
    echo [警告] pip 升级失败,但将继续安装依赖
)

echo [安装] 正在安装后端依赖...
.venv\Scripts\pip.exe install -r "%REQ_FILE%"
if errorlevel 1 goto :deps_failed
echo [完成] 项目依赖安装成功

echo.
echo ========================================
echo 重置完成!
echo ========================================
echo.
echo [成功] 虚拟环境已重置完成,可以开始使用
echo.
echo 后续操作:
echo   1. 运行 start.bat 启动后端（内置静态资源，端口 18088）
echo   2. 手动启动后端:
echo      cd backend ^&^& ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 18088
echo   3. 前端开发模式:
echo      cd frontend ^&^& npm install ^&^& npm run dev -- --host
echo.
echo 访问地址:
echo   - 前端界面: http://localhost:18088
echo   - 后端 OpenAPI: http://localhost:18088/docs
echo   - 健康检查: http://localhost:18088/health
echo.

pause
exit /b 0

:no_python
echo [错误] 未检测到 Python,请先安装 Python 3.8+
pause
exit /b 1

:cancelled
echo [取消] 用户取消操作
pause
exit /b 0

:missing_requirements
echo [错误] 未找到 backend\requirements.txt: %REQ_FILE%
pause
exit /b 1

:venv_failed
echo [错误] 创建虚拟环境失败
pause
exit /b 1

:deps_failed
echo [错误] 依赖安装失败
pause
exit /b 1
