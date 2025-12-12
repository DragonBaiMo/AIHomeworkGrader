"""
大模型客户端封装，支持真实请求与离线模拟模式。
"""
from __future__ import annotations

import json
import random
from typing import Any, Dict, Optional

import httpx

from config.settings import DEFAULT_MODEL_TIMEOUT
from app.service.rules import get_system_prompt
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
        system_prompt = get_system_prompt()
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": self._build_user_content(template, content),
            },
        ]
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.2,
        }
        last_exc: Optional[Exception] = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=DEFAULT_MODEL_TIMEOUT) as client:
                    resp = await client.post(self.api_url, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning("调用大模型失败或超时，第 %d 次重试：%s", attempt + 1, exc)
                if attempt == 2:
                    logger.error("大模型连续多次调用失败，终止本次评分。")
                    raise ModelError("模型调用失败或超时，请检查网络或稍后重试") from exc
        try:
            content_text = data["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            logger.error("模型返回结构异常：%s", exc)
            raise ModelError("模型返回数据结构异常，缺少 choices.message.content 字段") from exc
        try:
            parsed = self._parse_json_from_text(content_text)
        except Exception as exc:  # noqa: BLE001
            logger.error("解析模型 JSON 失败：%s", exc)
            raise ModelError("模型未按要求返回合法 JSON，请检查提示词设置") from exc
        return self._normalize_response(parsed)

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
    def _build_user_content(template_text: str, homework_text: str) -> str:
        """
        组装 User Prompt。

        约定提示词文件中使用 {{HOMEWORK_TEXT}} 作为正文占位符；若未包含占位符，则自动附加正文区块。
        """
        placeholder = "{{HOMEWORK_TEXT}}"
        if placeholder in template_text:
            return template_text.replace(placeholder, homework_text)
        return f"{template_text}\n\n【学生作业正文】\n{homework_text}"

    @staticmethod
    def _parse_json_from_text(text: str) -> Dict[str, Any]:
        """从模型输出文本中提取 JSON 对象。

        若存在 Markdown 代码块或额外说明，将自动截取第一个花括号到最后一个花括号之间的内容。
        """
        if not text:
            raise ValueError("模型输出为空")
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("未在模型输出中找到 JSON 对象")
        snippet = text[start : end + 1]
        return json.loads(snippet)

    @staticmethod
    def _normalize_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """将接口返回的评分结果标准化，并对分数做范围约束。"""
        try:
            score_raw = data.get("score")
            dim = data.get("dimension", {}) or {}
            structure_raw = dim.get("structure")
            content_raw = dim.get("content")
            expression_raw = dim.get("expression")

            def to_float(v: Any) -> float:
                if v is None:
                    raise ValueError("分数字段为空")
                return float(v)

            def to_int(v: Any) -> int:
                if v is None:
                    raise ValueError("分数字段为空")
                return int(float(v))

            def clamp_0_100(num: float) -> float:
                return max(0.0, min(100.0, num))

            score = clamp_0_100(to_float(score_raw))
            structure = int(clamp_0_100(to_float(structure_raw)))
            content = int(clamp_0_100(to_float(content_raw)))
            expression = int(clamp_0_100(to_float(expression_raw)))

            comment = data.get("comment")
            if comment is None or not str(comment).strip():
                raise ValueError("评语字段为空")

            return {
                "score": score,
                "comment": str(comment).strip(),
                "dimension": {
                    "structure": structure,
                    "content": content,
                    "expression": expression,
                },
                "model": data.get("model"),
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("评分结果解析失败：%s", exc)
            raise ModelError("模型返回数据格式异常") from exc
