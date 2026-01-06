"""
实际调用 AI 模型测试评分标准生成功能。
使用硅基流动 API 进行测试（非交互式）。
"""
import asyncio
import json
import sys
sys.path.insert(0, ".")

from app.service.rubric_generator import generate_rubric, RubricGeneratorError


# 硅基流动配置
SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
SILICONFLOW_API_KEY = ""  # 需要填入有效的 API Key
SILICONFLOW_MODEL = "Qwen/Qwen2.5-7B-Instruct"


async def test_generate_rubric():
    """测试生成评分标准。"""

    # 测试用例：Python 编程作业
    description = """
    请为大学《Python程序设计》课程的期末大作业设计评分标准。

    作业要求：
    - 学生需要完成一个数据分析项目
    - 包含数据清洗、可视化、统计分析
    - 需要提交代码和分析报告

    总分：100分

    评分维度建议：
    1. 代码质量（规范性、可读性、注释）
    2. 功能实现（数据处理、可视化、分析方法）
    3. 报告质量（结构、内容、表述）
    """

    print("=" * 60)
    print("测试 AI 生成评分标准")
    print("=" * 60)
    print(f"API: {SILICONFLOW_API_URL}")
    print(f"Model: {SILICONFLOW_MODEL}")
    print("-" * 60)

    print("\n正在调用 AI 生成评分标准...")

    try:
        result = await generate_rubric(
            description=description,
            api_url=SILICONFLOW_API_URL,
            api_key=SILICONFLOW_API_KEY,
            model_name=SILICONFLOW_MODEL,
        )

        print("\n" + "=" * 60)
        print("生成成功！")
        print("=" * 60)
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 验证结构
        print("\n" + "-" * 60)
        print("结构验证:")
        print(f"  category_key: {result.get('category_key')}")
        print(f"  display_name: {result.get('display_name')}")
        print(f"  sections 数量: {len(result.get('sections', []))}")

        total = 0
        for section in result.get("sections", []):
            section_score = section.get("max_score", 0)
            total += section_score
            print(f"    - {section.get('key')}: {section_score}分")
            for item in section.get("items", []):
                print(f"        · {item.get('key')}: {item.get('max_score')}分")

        print(f"  总分: {total}")
        print("-" * 60)

        if total == 100:
            print("✓ 总分验证通过")
        else:
            print(f"✗ 总分不正确，期望 100，实际 {total}")

        return True

    except RubricGeneratorError as e:
        print(f"\n生成失败: {e}")
        return False
    except Exception as e:
        print(f"\n发生错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_generate_rubric())
    sys.exit(0 if success else 1)
