@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "BASE_DIR=%%~fI"
set "BACKEND_DIR=%BASE_DIR%\backend"
set "APP_PORT=18088"
set "VENV_PY=%BASE_DIR%\.venv\Scripts\python.exe"
set "VENV_SITE=%BASE_DIR%\.venv\Lib\site-packages"
set "RESET_ENV_BAT=%SCRIPT_DIR%reset-env.bat"

echo ========================================
echo AI 作业批改工具 - 启动脚本
echo ========================================
echo.

cd /d "%BASE_DIR%"

if not exist "%VENV_PY%" goto :missing_venv

if not exist "%VENV_SITE%\fastapi" goto :missing_deps

if not exist "%VENV_SITE%\uvicorn" goto :missing_uvicorn

echo [启动] 正在启动 AI 作业批改工具...
echo.
echo 系统信息:
echo   - 后端: FastAPI + Uvicorn
echo   - 前端: Vue3 (Vite 打包后静态托管)
echo   - 端口: %APP_PORT%
echo   - 功能: 批量作业文件（docx/Markdown/txt）批改与导出
echo.
echo 访问地址:
echo   - 前端界面: http://localhost:%APP_PORT%
echo   - 后端 OpenAPI: http://localhost:%APP_PORT%/docs
echo   - 健康检查: http://localhost:%APP_PORT%/health
echo.
echo ========================================
echo.
echo [提示] 按 Ctrl+C 停止服务
echo.

pushd "%BACKEND_DIR%"
set PYTHONPATH=%BACKEND_DIR%
"%VENV_PY%" -m uvicorn app.main:app --host 0.0.0.0 --port %APP_PORT%
popd

echo.
echo ========================================
if %errorlevel% neq 0 goto :service_failed
echo [信息] 服务已停止
goto :service_done

:service_failed
echo [错误] 服务异常退出，错误代码: %errorlevel%
:service_done
echo ========================================
pause
exit /b %errorlevel%

:missing_venv
echo [错误] 虚拟环境不存在或不完整: %BASE_DIR%\.venv
echo [提示] 请先运行 "%RESET_ENV_BAT%" 初始化环境
pause
exit /b 1

:missing_deps
echo [错误] 项目依赖未安装或不完整
echo [提示] 请先运行 "%RESET_ENV_BAT%" 初始化环境
pause
exit /b 1

:missing_uvicorn
echo [错误] uvicorn 未安装
echo [提示] 请先运行 "%RESET_ENV_BAT%" 初始化环境
pause
exit /b 1
