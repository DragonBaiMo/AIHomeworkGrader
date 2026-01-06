"""
测试 AI 评分标准生成服务。
"""
import json
import pytest
from unittest.mock import AsyncMock, patch

from app.service.rubric_generator import (
    RubricGeneratorError,
    _extract_json_from_response,
    _extract_total_score,
    _validate_rubric_structure,
    generate_rubric,
)


class TestExtractTotalScore:
    """测试总分提取。"""

    def test_满分格式(self):
        assert _extract_total_score("满分100分") == 100
        assert _extract_total_score("满分：100分") == 100
        assert _extract_total_score("满分:100") == 100

    def test_总分格式(self):
        assert _extract_total_score("总分60分") == 60
        assert _extract_total_score("总分：80") == 80

    def test_其他格式(self):
        assert _extract_total_score("100分制") == 100
        assert _extract_total_score("共50分") == 50
        assert _extract_total_score("60分满分") == 60

    def test_无总分(self):
        assert _extract_total_score("请设计一个评分标准") is None


class TestExtractJsonFromResponse:
    """测试 JSON 提取。"""

    def test_直接json(self):
        text = '{"category_key": "test"}'
        result = _extract_json_from_response(text)
        assert result["category_key"] == "test"

    def test_代码块json(self):
        text = '```json\n{"category_key": "test"}\n```'
        result = _extract_json_from_response(text)
        assert result["category_key"] == "test"

    def test_混合文本中的json(self):
        text = '好的，这是生成的结果：\n{"category_key": "test"}\n请确认。'
        result = _extract_json_from_response(text)
        assert result["category_key"] == "test"

    def test_无法解析(self):
        with pytest.raises(RubricGeneratorError, match="无法从模型响应中解析"):
            _extract_json_from_response("这不是JSON")


class TestValidateRubricStructure:
    """测试结构验证。"""

    def test_有效结构(self):
        rubric = {
            "category_key": "test",
            "display_name": "测试作业",
            "sections": [
                {
                    "key": "维度1",
                    "max_score": 60,
                    "items": [
                        {"key": "细则1", "max_score": 30, "description": "描述1"},
                        {"key": "细则2", "max_score": 30, "description": "描述2"},
                    ],
                },
                {
                    "key": "维度2",
                    "max_score": 40,
                    "items": [
                        {"key": "细则3", "max_score": 40, "description": "描述3"},
                    ],
                },
            ],
        }
        errors = _validate_rubric_structure(rubric, 100)
        assert errors == []

    def test_总分不匹配(self):
        rubric = {
            "category_key": "test",
            "display_name": "测试",
            "sections": [
                {"key": "维度1", "max_score": 50, "items": [{"key": "x", "max_score": 50, "description": "d"}]},
            ],
        }
        errors = _validate_rubric_structure(rubric, 100)
        assert any("不等于总分" in e for e in errors)

    def test_维度分数不匹配(self):
        rubric = {
            "category_key": "test",
            "display_name": "测试",
            "sections": [
                {
                    "key": "维度1",
                    "max_score": 100,
                    "items": [
                        {"key": "细则1", "max_score": 30, "description": "描述1"},
                        {"key": "细则2", "max_score": 30, "description": "描述2"},
                    ],
                },
            ],
        }
        errors = _validate_rubric_structure(rubric, 100)
        assert any("细则分数之和" in e for e in errors)

    def test_缺少字段(self):
        rubric = {"sections": []}
        errors = _validate_rubric_structure(rubric, 100)
        assert any("category_key" in e for e in errors)
        assert any("display_name" in e for e in errors)


class TestGenerateRubric:
    """测试完整生成流程（使用 mock）。"""

    @pytest.mark.asyncio
    async def test_缺少总分描述(self):
        with pytest.raises(RubricGeneratorError, match="请在描述中指定总分"):
            await generate_rubric(
                description="设计一个Python作业评分标准",
                api_url="https://api.example.com/v1/chat/completions",
                api_key="test-key",
                model_name="gpt-4",
            )

    @pytest.mark.asyncio
    async def test_成功生成(self):
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "category_key": "python_hw",
                                "display_name": "Python作业",
                                "sections": [
                                    {
                                        "key": "代码质量",
                                        "max_score": 50,
                                        "items": [
                                            {"key": "代码规范", "max_score": 25, "description": "代码符合PEP8规范"},
                                            {"key": "可读性", "max_score": 25, "description": "代码可读性强"},
                                        ],
                                    },
                                    {
                                        "key": "功能实现",
                                        "max_score": 50,
                                        "items": [
                                            {"key": "功能完整", "max_score": 50, "description": "功能全部实现"},
                                        ],
                                    },
                                ],
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_resp = AsyncMock()
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = lambda: None
            mock_instance.post.return_value = mock_resp

            result = await generate_rubric(
                description="设计Python作业评分标准，满分100分",
                api_url="https://api.example.com/v1/chat/completions",
                api_key="test-key",
                model_name="gpt-4",
            )

            assert result["category_key"] == "python_hw"
            assert result["display_name"] == "Python作业"
            assert len(result["sections"]) == 2
            assert "docx_validation" in result  # 应自动添加


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
