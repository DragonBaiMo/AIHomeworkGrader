"""
大模型客户端封装，支持真实请求与离线模拟模式。
"""
from __future__ import annotations

import random
from typing import Any, Dict, Optional

import httpx

from config.settings import DEFAULT_MODEL_TIMEOUT
from app.util.logger import logger


class ModelError(Exception):
    """大模型调用异常。"""


class AIClient:
    """封装模型调用逻辑，兼顾真实接口与离线模拟。"""

    def __init__(self, api_url: Optional[str], api_key: Optional[str], model_name: Optional[str], mock: bool = False) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name or "demo-model"
        self.mock = mock or not api_url

    async def grade(self, content: str, template: str) -> Dict[str, Any]:
        """对正文内容进行评分，返回标准化字典。"""
        if self.mock:
            logger.info("启用离线模拟评分，跳过真实调用。")
            return self._mock_grade(content, template)
        if not self.api_url:
            raise ModelError("未配置模型接口地址")
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {
            "model": self.model_name,
            "template": template,
            "content": content,
        }
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_MODEL_TIMEOUT) as client:
                resp = await client.post(self.api_url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            logger.error("调用大模型失败：%s", exc)
            raise ModelError("模型调用失败，请检查 API 配置或网络") from exc
        return self._normalize_response(data)

    def _mock_grade(self, content: str, template: str) -> Dict[str, Any]:
        """生成伪造评分结果，便于离线演示。"""
        base_score = random.randint(75, 95)
        structure = min(100, max(60, base_score + random.randint(-5, 5)))
        analysis = {
            "score": float(base_score),
            "comment": f"基于模版[{template}]的自动评语：结构清晰，内容完整，表达流畅。",
            "dimension": {
                "structure": structure,
                "content": min(100, max(60, base_score + random.randint(-8, 8))),
                "expression": min(100, max(60, base_score + random.randint(-10, 10))),
            },
            "model": self.model_name,
        }
        return analysis

    @staticmethod
    def _normalize_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """将接口返回的评分结果标准化。"""
        try:
            return {
                "score": float(data.get("score")),
                "comment": data.get("comment"),
                "dimension": {
                    "structure": int(data.get("dimension", {}).get("structure")),
                    "content": int(data.get("dimension", {}).get("content")),
                    "expression": int(data.get("dimension", {}).get("expression")),
                },
                "model": data.get("model"),
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("评分结果解析失败：%s", exc)
            raise ModelError("模型返回数据格式异常") from exc

