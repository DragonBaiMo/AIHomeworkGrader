"""
日志模块，统一配置日志格式与输出方式。
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from config.settings import DATA_DIR

LOG_FILE_NAME = "runtime.log"
LOG_LEVEL = logging.INFO
MAX_BYTES = 2 * 1024 * 1024
BACKUP_COUNT = 3


def setup_logger() -> logging.Logger:
    """初始化日志记录器，输出到控制台与滚动文件。"""
    logger = logging.getLogger("ai_homework_grader")
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_dir = DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=str(log_dir / LOG_FILE_NAME),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


logger: Optional[logging.Logger] = setup_logger()
