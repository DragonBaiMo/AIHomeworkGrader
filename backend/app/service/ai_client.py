"""
大模型客户端封装，支持真实请求与离线模拟模式。
"""
from __future__ import annotations

import json
import random
from typing import Any, Dict, Optional

import httpx

from config.settings import DEFAULT_MODEL_TIMEOUT
from app.service.prompt_builder import RubricExpected
from app.util.logger import logger


class ModelError(Exception):
    """大模型调用异常。"""

    def __init__(self, message: str, *, raw_response: str | None = None) -> None:
        super().__init__(message)
        self.raw_response = raw_response


class AIClient:
    """封装模型调用逻辑，兼顾真实接口与离线模拟。"""

    def __init__(self, api_url: Optional[str], api_key: Optional[str], model_name: Optional[str], mock: bool = False) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name or "demo-model"
        self.mock = mock or not api_url

    async def grade(
        self,
        content: str,
        system_prompt: str,
        template: str,
        expected: RubricExpected,
        score_target_max: float,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """对正文内容进行评分，返回原始解析 + 标准化字典。"""
        if self.mock:
            logger.info("启用离线模拟评分，跳过真实调用。")
            return self._mock_grade(template, expected, score_target_max)
        if not self.api_url:
            raise ModelError("未配置模型接口地址")
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
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
            raise ModelError("模型未按要求返回合法 JSON，请检查提示词设置", raw_response=content_text) from exc
        normalized = self._normalize_response(parsed, expected, score_target_max)
        return parsed, normalized

    def _mock_grade(self, template: str, expected: RubricExpected, score_target_max: float) -> Dict[str, Any]:
        """生成伪造评分结果（schema_version=2），便于离线演示。"""
        sections: list[dict] = []
        score_rubric = 0.0
        for sec in expected.sections:
            items_out: list[dict] = []
            sec_score = 0.0
            for item in sec.items:
                max_v = float(item.max_score)
                got = round(max(0.0, min(max_v, max_v - random.random() * max(1.0, max_v * 0.3))), 2)
                sec_score += got
                items_out.append(
                    {
                        "name": item.name,
                        "max_score": max_v,
                        "score": got,
                        "comment": "示例：扣分原因需具体说明。" if got < max_v else "示例：表现良好。",
                    }
                )
            score_rubric += sec_score
            sections.append(
                {
                    "name": sec.name,
                    "max_score": float(sec.max_score),
                    "score": sec_score,
                    "comment": "示例：本维度总体评价。",
                    "items": items_out,
                }
            )
        score = round(score_rubric * float(score_target_max) / float(expected.rubric_max or 1.0), 2)
        return {
            "schema_version": 2,
            "category_name": expected.category_name,
            "score_target_max": float(score_target_max),
            "score_rubric_max": float(expected.rubric_max),
            "score_rubric": score_rubric,
            "score": score,
            "comment": f"基于模板[{template}]的模拟评语：结构较清晰，内容较完整，表达较流畅。",
            "sections": sections,
            "model": self.model_name,
        }

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

        解析策略：
        1) 若存在 Markdown 代码块（```...```），优先提取第一个看起来像 JSON 的代码块内容；
        2) 否则回退为截取第一个“{”到最后一个“}”之间的内容。
        """
        if not text:
            raise ValueError("模型输出为空")

        # 优先解析 Markdown 代码块
        fence = "```"
        start_idx = 0
        while True:
            fence_start = text.find(fence, start_idx)
            if fence_start == -1:
                break
            lang_end = text.find("\n", fence_start + len(fence))
            if lang_end == -1:
                break
            fence_end = text.find(fence, lang_end + 1)
            if fence_end == -1:
                break
            block = text[lang_end + 1 : fence_end].strip()
            if block.startswith("{") and block.endswith("}"):
                return json.loads(block)
            start_idx = fence_end + len(fence)

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("未在模型输出中找到 JSON 对象")
        snippet = text[start : end + 1]
        return json.loads(snippet)

    @staticmethod
    def _normalize_response(data: Dict[str, Any], expected: RubricExpected, score_target_max: float) -> Dict[str, Any]:
        """将接口返回的评分结果标准化（schema_version=2），并按目标满分进行比例换算。

        注意：模型输出只要求包含细则得分与评语；所有总分字段由后端根据评分规则自动计算。
        """
        try:
            def to_float(v: Any) -> float:
                if v is None:
                    raise ValueError("分数字段为空")
                return float(v)

            def clamp_min_max(num: float, min_v: float, max_v: float) -> float:
                return max(min_v, min(max_v, num))

            comment = data.get("comment")
            if comment is None or not str(comment).strip():
                raise ValueError("评语字段为空")

            schema_version = int(to_float(data.get("schema_version")))
            if schema_version != 2:
                raise ValueError("schema_version 必须为 2")

            if float(score_target_max) <= 0:
                raise ValueError("score_target_max 非法")
            score_rubric_max = float(expected.rubric_max)
            if score_rubric_max <= 0:
                raise ValueError("评分规则总分非法")

            sections = data.get("sections")
            if not isinstance(sections, list) or not sections:
                raise ValueError("sections 必须为非空数组")

            # 将模型输出按“名称”对齐到期望结构，并强制校验不可多不可少。
            model_sections_by_name: dict[str, Any] = {}
            for sec in sections:
                if not isinstance(sec, dict):
                    continue
                name = str(sec.get("name") or "").strip()
                if name:
                    model_sections_by_name[name] = sec

            if len(model_sections_by_name) != len(expected.sections):
                raise ValueError("sections 数量与评分规则不一致")

            normalized_sections: list[dict] = []
            score_rubric = 0.0
            for sec_expected in expected.sections:
                sec_model = model_sections_by_name.get(sec_expected.name)
                if not isinstance(sec_model, dict):
                    raise ValueError(f"缺失评分维度：{sec_expected.name}")
                items = sec_model.get("items")
                if not isinstance(items, list):
                    raise ValueError(f"维度“{sec_expected.name}”的 items 非法")
                model_items_by_name: dict[str, Any] = {}
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    item_name = str(item.get("name") or "").strip()
                    if item_name:
                        model_items_by_name[item_name] = item
                if len(model_items_by_name) != len(sec_expected.items):
                    raise ValueError(f"维度“{sec_expected.name}”的细则数量与评分规则不一致")

                sec_score = 0.0
                normalized_items: list[dict] = []
                for item_expected in sec_expected.items:
                    item_model = model_items_by_name.get(item_expected.name)
                    if not isinstance(item_model, dict):
                        raise ValueError(f"缺失评分细则：{sec_expected.name} / {item_expected.name}")
                    item_score = clamp_min_max(to_float(item_model.get("score")), 0.0, float(item_expected.max_score))
                    item_comment = str(item_model.get("comment") or "").strip()
                    if not item_comment:
                        item_comment = "未提供细则扣分原因。"
                    sec_score += float(item_score)
                    normalized_items.append(
                        {
                            "name": item_expected.name,
                            "max_score": float(item_expected.max_score),
                            "score": float(item_score),
                            "comment": item_comment,
                        }
                    )

                score_rubric += sec_score
                sec_comment = str(sec_model.get("comment") or "").strip() or "未提供维度总体评价。"
                normalized_sections.append(
                    {
                        "name": sec_expected.name,
                        "max_score": float(sec_expected.max_score),
                        "score": float(sec_score),
                        "comment": sec_comment,
                        "items": normalized_items,
                    }
                )

            score_rubric = clamp_min_max(score_rubric, 0.0, score_rubric_max)
            score = round(score_rubric * float(score_target_max) / score_rubric_max, 2)

            return {
                "schema_version": 2,
                "category_name": expected.category_name,
                "score_target_max": float(score_target_max),
                "score_rubric_max": score_rubric_max,
                "score_rubric": score_rubric,
                "score": score,
                "comment": str(comment).strip(),
                "sections": normalized_sections,
                "model": data.get("model"),
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("评分结果解析失败：%s", exc)
            raise ModelError("模型返回数据格式异常") from exc
