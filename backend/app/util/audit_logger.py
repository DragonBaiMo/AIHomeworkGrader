"""
审计日志模块，负责把批改全流程（请求、提示词、模型交互、异常）写入磁盘归档。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from config.settings import DATA_DIR


class AuditLogger:
    """可持久化地记录批改过程相关信息。"""

    def __init__(self, batch_id: str) -> None:
        base = DATA_DIR / "logs" / batch_id
        self.base = base
        self.base.mkdir(parents=True, exist_ok=True)
        self.prompts_dir = self.base / "prompts"
        self.responses_dir = self.base / "model-responses"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        self._operations_path = self.base / "operations.log"

    def log_operation(self, message: str) -> None:
        timestamp = datetime.utcnow().isoformat()
        line = f"[{timestamp}] {message}\n"
        append_to_file(self._operations_path, line)

    def save_meta(self, payload: dict[str, Any]) -> None:
        meta_path = self.base / "request_meta.json"
        payload["timestamp"] = datetime.utcnow().isoformat()
        meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_prompts(self, system_prompt: str, user_prompt: str) -> None:
        (self.prompts_dir / "system_prompt.txt").write_text(system_prompt, encoding="utf-8")
        (self.prompts_dir / "user_prompt.txt").write_text(user_prompt, encoding="utf-8")

    def save_model_interaction(
        self,
        file_name: str,
        system_prompt: str,
        user_prompt: str,
        response: dict[str, Any],
        *,
        model_id: str | None = None,
        resolved_user_prompt: str | None = None,
        raw_response: str | None = None,
        status: str = "success",
    ) -> None:
        safe_name = file_name.replace(" ", "_")
        suffix = f"_{model_id}" if model_id else ""
        target = self.responses_dir / f"{safe_name}{suffix}_{datetime.utcnow().strftime('%H%M%S')}.json"
        interaction = {
            "file": file_name,
            "model_id": model_id,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "resolved_user_prompt": resolved_user_prompt,
            "response": response,
            "raw_response": raw_response,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        target.write_text(json.dumps(interaction, ensure_ascii=False, indent=2), encoding="utf-8")

    def append_error(self, file_name: str, error_message: str) -> None:
        error_path = self.base / "errors.log"
        line = f"[{datetime.utcnow().isoformat()}] {file_name} -> {error_message}\n"
        append_to_file(error_path, line)


def append_to_file(path: Path, text: str) -> None:
    """辅助：追加文本到文件（会新建）。"""
    if not path.exists():
        path.write_text(text, encoding="utf-8")
        return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)
