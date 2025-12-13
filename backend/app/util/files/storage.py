"""上传文件存储与批次 ID 生成逻辑。"""
from __future__ import annotations

import random
import string
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple

from fastapi import UploadFile

from config.settings import UPLOAD_DIR
from app.util.logger import logger


def generate_batch_id(prefix: str = "batch") -> str:
    """生成批次 ID，格式为 prefix-年月日时分秒-随机串。"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}-{timestamp}-{rand}"


def save_upload_files(batch_id: str, files: Iterable[UploadFile]) -> Tuple[Path, list[Path]]:
    """将上传的文件保存到本地批次目录。"""
    batch_dir = UPLOAD_DIR / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    stored_paths: list[Path] = []
    for file in files:
        target = batch_dir / file.filename
        with target.open("wb") as f:
            content = file.file.read()
            f.write(content)
        logger.info("保存上传文件：%s", target)
        stored_paths.append(target)
    return batch_dir, stored_paths
