"""
AI 作业批改工具 - 可执行文件启动入口

本模块用于 PyInstaller 打包后的启动入口，功能包括：
1. 启动 FastAPI 后端服务
2. 自动打开默认浏览器访问前端界面
3. 优雅处理服务关闭
"""
from __future__ import annotations

import os
import sys
import time
import signal
import socket
import threading
import webbrowser
from pathlib import Path
from contextlib import closing


def get_base_dir() -> Path:
    """
    获取应用基础目录。
    
    PyInstaller 打包后，sys._MEIPASS 指向临时解压目录，
    未打包时使用当前文件所在目录。
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后运行
        return Path(sys._MEIPASS)
    else:
        # 直接运行源码
        return Path(__file__).resolve().parent


def find_available_port(start_port: int = 18088) -> int:
    """
    查找可用端口。
    
    从指定端口开始尝试，如果被占用则递增查找，
    最多尝试 100 个端口。
    
    Args:
        start_port: 起始端口号
        
    Returns:
        可用的端口号
        
    Raises:
        RuntimeError: 未找到可用端口时抛出
    """
    for port in range(start_port, start_port + 100):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            result = sock.connect_ex(('127.0.0.1', port))
            if result != 0:
                return port
    raise RuntimeError(f"未找到可用端口（尝试范围：{start_port}-{start_port + 99}）")


def open_browser_delayed(url: str, delay: float = 2.0) -> None:
    """
    延迟打开浏览器。
    
    在后台线程中等待指定时间后打开浏览器，
    确保服务已启动完成。
    
    Args:
        url: 要打开的页面地址
        delay: 延迟秒数
    """
    def _open():
        time.sleep(delay)
        print(f"\n[信息] 正在打开浏览器: {url}")
        webbrowser.open(url)
    
    thread = threading.Thread(target=_open, daemon=True)
    thread.start()


def setup_signal_handlers() -> None:
    """
    设置信号处理器，确保优雅退出。
    """
    def signal_handler(signum, frame):
        print("\n[信息] 正在关闭服务...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    """
    主入口函数。
    
    1. 设置环境变量和路径
    2. 查找可用端口
    3. 启动 FastAPI 服务
    4. 自动打开浏览器
    """
    print("=" * 50)
    print("AI 作业批改工具 - 可执行版本")
    print("=" * 50)
    print()
    
    # 获取基础目录
    base_dir = get_base_dir()
    print(f"[信息] 应用目录: {base_dir}")
    
    # 设置环境变量
    os.environ['PYTHONPATH'] = str(base_dir)
    
    # 切换工作目录到应用目录
    os.chdir(base_dir)
    
    # 查找可用端口
    port = find_available_port(18088)
    print(f"[信息] 使用端口: {port}")
    
    # 设置信号处理
    setup_signal_handlers()
    
    # 延迟打开浏览器
    url = f"http://localhost:{port}"
    open_browser_delayed(url)
    
    print()
    print("系统信息:")
    print("  - 后端: FastAPI + Uvicorn")
    print("  - 前端: Vue3 (静态托管)")
    print(f"  - 端口: {port}")
    print()
    print("访问地址:")
    print(f"  - 前端界面: {url}")
    print(f"  - 后端 API: {url}/docs")
    print()
    print("[提示] 关闭本窗口即可停止服务")
    print("=" * 50)
    print()
    
    # 动态导入并启动服务
    # 这样可以确保在打包时正确处理依赖
    import uvicorn
    from app.main import app
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
