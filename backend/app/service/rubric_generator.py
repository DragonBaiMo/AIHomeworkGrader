"""
AI 评分标准生成服务。
根据老师的文字描述，自动生成符合项目格式的评分标准 JSON。
"""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.util.logger import logger

# 生成评分标准的系统提示词
RUBRIC_GEN_SYSTEM_PROMPT = """你是一名专业的教育评估专家，擅长设计作业评分标准。

你的任务是根据用户的描述，生成结构化的评分标准 JSON。

## 输出格式要求

你必须严格按照以下 JSON 格式输出，不要包含任何其他内容：

```json
{
  "category_key": "英文小写下划线命名，如 python_assignment",
  "display_name": "中文显示名称，如 Python编程作业",
  "sections": [
    {
      "key": "维度名称，如 代码质量",
      "max_score": 40,
      "items": [
        {
          "key": "细则名称，如 代码规范",
          "max_score": 20,
          "description": "详细的评分要求描述，说明如何评判该项",
          "is_deduction": false
        }
      ]
    }
  ]
}
```

## 设计原则

1. **维度设计**：每个 section 代表一个大的评分维度，通常 3-5 个维度为宜
2. **细则设计**：每个 item 是具体的评分细则，每个维度下 2-4 个细则
3. **分数分配**：
   - 各维度的 max_score 之和必须等于用户指定的总分（仅计算非扣分项）
   - 每个维度下各非扣分项 item 的 max_score 之和必须等于该维度的 max_score
4. **描述要求**：description 应具体、可操作，便于评分时判断
5. **命名规范**：category_key 使用英文小写+下划线，从描述中提取关键词
6. **扣分项设计**（可选）：
   - 如果用户描述中提到了需要扣分的情况（如格式问题、抄袭、迟交等），应添加扣分项
   - 扣分项设置 `is_deduction: true`，其 max_score 表示最大扣分额度
   - 扣分项的分数不计入维度总分，而是从最终得分中扣除
   - 如果用户未提及扣分情况，则无需添加扣分项

## 注意事项

- 仅输出 JSON，不要有任何解释文字
- JSON 必须格式正确，可被直接解析
- 分数必须是数字，不能是字符串
- is_deduction 字段可选，默认为 false（表示得分项）
"""

RUBRIC_GEN_USER_TEMPLATE = """请根据以下描述生成评分标准：

---
{description}
---

要求：
- 总分必须是 {total_score} 分
- 各维度分数之和 = {total_score}
- 每个维度下各细则分数之和 = 该维度分数

只输出 JSON，不要有其他内容。"""


class RubricGeneratorError(Exception):
    """评分标准生成异常。"""

    pass


def _extract_json_from_response(text: str) -> dict[str, Any]:
    """从模型响应中提取 JSON 对象。"""
    # 尝试直接解析
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 尝试提取 ```json ... ``` 代码块
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 尝试提取 { ... } 部分
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise RubricGeneratorError("无法从模型响应中解析 JSON")


def _extract_total_score(description: str) -> int | None:
    """从描述中提取总分。"""
    # 匹配常见的总分描述模式
    patterns = [
        r"满分\s*[:：]?\s*(\d+)\s*分?",
        r"总分\s*[:：]?\s*(\d+)\s*分?",
        r"(\d+)\s*分\s*满分",
        r"(\d+)\s*分\s*制",
        r"共\s*(\d+)\s*分",
    ]
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            return int(match.group(1))
    return None


def _validate_rubric_structure(rubric: dict[str, Any], expected_total: int) -> list[str]:
    """验证生成的评分标准结构和分数。返回错误列表。"""
    errors = []

    # 检查必要字段
    required_fields = ["category_key", "display_name", "sections"]
    for field in required_fields:
        if field not in rubric:
            errors.append(f"缺少必要字段: {field}")

    if "sections" not in rubric:
        return errors

    sections = rubric.get("sections", [])
    if not isinstance(sections, list) or len(sections) == 0:
        errors.append("sections 必须是非空数组")
        return errors

    # 检查总分（仅计算非扣分项）
    total = 0
    for idx, section in enumerate(sections):
        if "key" not in section:
            errors.append(f"第 {idx + 1} 个维度缺少 key")
        if "max_score" not in section:
            errors.append(f"第 {idx + 1} 个维度缺少 max_score")
            continue

        section_score = section.get("max_score", 0)
        total += section_score

        # 检查 items 分数之和（仅计算非扣分项）
        items = section.get("items", [])
        if not isinstance(items, list) or len(items) == 0:
            errors.append(f"维度「{section.get('key', idx + 1)}」的 items 必须是非空数组")
            continue

        # 仅对非扣分项求和
        items_total = sum(
            item.get("max_score", 0)
            for item in items
            if not item.get("is_deduction", False)
        )
        if abs(items_total - section_score) > 0.01:
            errors.append(
                f"维度「{section.get('key')}」的非扣分细则分数之和 ({items_total}) 不等于维度分数 ({section_score})"
            )

        # 检查 items 必要字段
        for item_idx, item in enumerate(items):
            if "key" not in item:
                errors.append(f"维度「{section.get('key')}」第 {item_idx + 1} 个细则缺少 key")
            if "max_score" not in item:
                errors.append(f"维度「{section.get('key')}」第 {item_idx + 1} 个细则缺少 max_score")
            if "description" not in item:
                errors.append(f"维度「{section.get('key')}」第 {item_idx + 1} 个细则缺少 description")

    if abs(total - expected_total) > 0.01:
        errors.append(f"各维度分数之和 ({total}) 不等于总分 ({expected_total})")

    return errors


async def generate_rubric(
    description: str,
    api_url: str,
    api_key: str | None,
    model_name: str,
    total_score: int | None = None,
) -> dict[str, Any]:
    """
    根据描述生成评分标准。

    Args:
        description: 老师的文字描述
        api_url: OpenAI 兼容 API 地址
        api_key: API 密钥
        model_name: 模型名称
        total_score: 指定总分（可选，未指定时从描述中提取）

    Returns:
        生成的评分标准 JSON（符合 prompt_config.json 中 categories 下单个分类的格式）

    Raises:
        RubricGeneratorError: 生成失败或格式校验失败
    """
    # 提取或验证总分
    extracted_score = _extract_total_score(description)
    if total_score is None:
        total_score = extracted_score
    if total_score is None:
        raise RubricGeneratorError(
            "请在描述中指定总分，例如「满分100分」或「总分60分」"
        )

    logger.info("开始生成评分标准，总分=%d，描述长度=%d", total_score, len(description))

    # 构建请求
    user_prompt = RUBRIC_GEN_USER_TEMPLATE.format(
        description=description.strip(),
        total_score=total_score,
    )

    messages = [
        {"role": "system", "content": RUBRIC_GEN_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.3,  # 较低温度以获得更稳定的结构化输出
        "max_tokens": 4096,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(api_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("API 请求失败: %s", e)
        raise RubricGeneratorError(f"API 请求失败: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error("网络请求错误: %s", e)
        raise RubricGeneratorError(f"网络请求错误: {e}")
    except Exception as e:
        logger.error("未知错误: %s", e)
        raise RubricGeneratorError(f"请求失败: {e}")

    # 提取响应内容
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        logger.error("响应格式异常: %s", data)
        raise RubricGeneratorError("模型响应格式异常")

    # 解析 JSON
    rubric = _extract_json_from_response(content)

    # 验证结构
    errors = _validate_rubric_structure(rubric, total_score)
    if errors:
        logger.warning("生成的评分标准校验失败: %s", errors)
        raise RubricGeneratorError(
            "生成的评分标准格式有误:\n" + "\n".join(f"- {e}" for e in errors)
        )

    # 添加默认的 docx_validation 配置
    rubric["docx_validation"] = {
        "enabled": False,
        "allowed_font_keywords": [],
        "allowed_font_size_pts": [],
        "font_size_tolerance": 0.5,
        "target_line_spacing": None,
        "line_spacing_tolerance": None,
    }

    logger.info(
        "评分标准生成成功: category_key=%s, sections=%d",
        rubric.get("category_key"),
        len(rubric.get("sections", [])),
    )

    return rubric
