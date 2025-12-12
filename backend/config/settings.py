"""
全局配置模块，集中维护运行相关的基础参数。
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
DATA_DIR: Final[Path] = BASE_DIR / "data"
UPLOAD_DIR: Final[Path] = DATA_DIR / "uploads"
STATIC_DIR: Final[Path] = BASE_DIR / "app" / "static"
TEMPLATE_DIR: Final[Path] = BASE_DIR / "app" / "templates"

# 默认模型请求超时（秒），按“5 分钟 / 人”预留足够评分时间
DEFAULT_MODEL_TIMEOUT: Final[int] = 300


def ensure_directories() -> None:
    """确保运行所需的目录存在，缺失时自动创建。"""
    for path in (DATA_DIR, UPLOAD_DIR):
        path.mkdir(parents=True, exist_ok=True)
