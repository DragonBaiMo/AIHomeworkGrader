@echo off
chcp 65001 >nul

:: 获取脚本所在目录和项目根目录
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%.."
set "BASE_DIR=%CD%"
popd

set "BACKEND_DIR=%BASE_DIR%\backend"
set "FRONTEND_DIR=%BASE_DIR%\frontend"
set "DIST_DIR=%BACKEND_DIR%\dist"
set "BUILD_DIR=%BACKEND_DIR%\build"

echo ========================================
echo AI 作业批改工具 - Windows 打包脚本
echo ========================================
echo.

cd /d "%BASE_DIR%"

:: ========================================
:: 步骤 1：检查 Python 环境
:: ========================================
echo [步骤 1/5] 检查 Python 环境...

set "PYTHON="
set "PIP="

if exist "%BASE_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON=%BASE_DIR%\.venv\Scripts\python.exe"
    set "PIP=%BASE_DIR%\.venv\Scripts\pip.exe"
    echo   使用虚拟环境 Python
    goto :python_found
)

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python 环境
    echo [提示] 请先安装 Python 3.9+ 或运行 reset-env.bat 创建虚拟环境
    goto :error
)
set "PYTHON=python"
set "PIP=pip"
echo   使用系统 Python

:python_found
"%PYTHON%" -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"
if errorlevel 1 (
    echo [错误] Python 版本过低，需要 3.9+
    goto :error
)
echo   Python 环境检查通过

:: ========================================
:: 步骤 2：安装打包依赖
:: ========================================
echo.
echo [步骤 2/5] 检查打包依赖...

"%PYTHON%" -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo   正在安装 PyInstaller...
    "%PIP%" install pyinstaller -q
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        goto :error
    )
)
echo   PyInstaller 已就绪

echo   安装后端依赖...
"%PIP%" install -q -r "%BACKEND_DIR%\requirements.txt"

:: ========================================
:: 步骤 3：构建前端
:: ========================================
echo.
echo [步骤 3/5] 构建前端...

where node >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js
    echo [提示] 请先安装 Node.js 16+
    goto :error
)

where npm >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 npm
    goto :error
)

cd /d "%FRONTEND_DIR%"

if not exist "node_modules\" (
    echo   安装前端依赖...
    call npm install
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败
        goto :error
    )
)

echo   执行前端构建...
call npm run build
if errorlevel 1 (
    echo [错误] 前端构建失败
    goto :error
)
echo   前端构建完成

:: ========================================
:: 步骤 4：打包后端
:: ========================================
echo.
echo [步骤 4/5] 打包后端...

cd /d "%BACKEND_DIR%"

if exist "%DIST_DIR%" (
    echo   清理旧的打包文件...
    rmdir /s /q "%DIST_DIR%"
)
if exist "%BUILD_DIR%" (
    rmdir /s /q "%BUILD_DIR%"
)

echo   开始打包（这可能需要几分钟）...
"%PYTHON%" -m PyInstaller build_config.spec --noconfirm
if errorlevel 1 (
    echo [错误] PyInstaller 打包失败
    goto :error
)

:: ========================================
:: 步骤 5：创建运行时数据目录
:: ========================================
echo.
echo [步骤 5/5] 整理打包产物...

set "OUTPUT_DIR=%DIST_DIR%\AI作业批改工具"
if exist "%OUTPUT_DIR%" (
    if not exist "%OUTPUT_DIR%\data" mkdir "%OUTPUT_DIR%\data"
    if not exist "%OUTPUT_DIR%\data\uploads" mkdir "%OUTPUT_DIR%\data\uploads"
    echo   创建运行时目录完成

    :: 创建快捷启动脚本
    (
        echo @echo off
        echo chcp 65001 ^> nul
        echo start "" "AI作业批改工具.exe"
    ) > "%OUTPUT_DIR%\启动.bat"
    echo   创建启动脚本完成
)

:: ========================================
:: 完成
:: ========================================
echo.
echo ========================================
echo [成功] 打包完成！
echo ========================================
echo.
echo 打包产物位置: %OUTPUT_DIR%
echo.
echo 使用方法:
echo   1. 将整个文件夹复制到目标机器
echo   2. 运行 "启动.bat" 或直接运行 "AI作业批改工具.exe"
echo   3. 浏览器会自动打开访问界面
echo.
echo 注意事项:
echo   - 确保目标机器有网络连接（用于调用 AI API）
echo   - 首次运行时会自动创建数据目录
echo   - 关闭控制台窗口即可停止服务
echo.
goto :end

:error
echo.
echo ========================================
echo [错误] 打包失败，请检查上述错误信息
echo ========================================
pause
exit /b 1

:end
pause
exit /b 0
