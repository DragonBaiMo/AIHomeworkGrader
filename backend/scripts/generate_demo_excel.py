"""生成演示用 Excel（用于肉眼检查导出样式与结构）。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.util.excel_utils import ExcelExporter


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成演示用 grade_result.xlsx / error_list.xlsx")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/_demo_batch"),
        help="输出目录（默认：backend/data/_demo_batch）",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    exporter = ExcelExporter(out_dir)

    rows = [
        {
            "file_name": "张三.docx",
            "student_id": "2025001",
            "student_name": "张三",
            "score": 55.0,
            "score_rubric": 45.0,
            "score_rubric_max": 60.0,
            "status": "成功",
            "error_message": None,
            "comment": "总体评语：结构清晰，建议补充数据来源。",
            "detail_json": json.dumps({"score_target_max": 60.0}, ensure_ascii=False),
            "aggregate_strategy": "mean",
            "grader_results": [
                {
                    "model_index": 1,
                    "api_url": "http://a",
                    "model_name": "main",
                    "status": "成功",
                    "score": 55,
                    "comment": "主模型评语：整体较好。",
                    "error_message": None,
                    "latency_ms": 100,
                    "sections": [
                        {
                            "name": "结构",
                            "max_score": 10,
                            "score": 8,
                            "comment": "结构不错",
                            "items": [
                                {"name": "标题", "max_score": 5, "score": 4, "comment": "标题清晰"},
                                {"name": "段落", "max_score": 5, "score": 4, "comment": "段落清楚"},
                            ],
                        },
                        {
                            "name": "内容",
                            "max_score": 20,
                            "score": 16,
                            "comment": "内容较完整",
                            "items": [
                                {"name": "论据", "max_score": 10, "score": 8, "comment": "论据基本充分"},
                                {"name": "逻辑", "max_score": 10, "score": 8, "comment": "逻辑顺畅"},
                            ],
                        },
                    ],
                },
                {
                    "model_index": 2,
                    "api_url": "http://b",
                    "model_name": "sub",
                    "status": "成功",
                    "score": 57,
                    "comment": "副模型1评语：表达更自然。",
                    "error_message": None,
                    "latency_ms": 120,
                    "sections": [
                        {
                            "name": "结构",
                            "max_score": 10,
                            "score": 9,
                            "comment": "结构更好",
                            "items": [
                                {"name": "标题", "max_score": 5, "score": 5, "comment": "很好"},
                                {"name": "段落", "max_score": 5, "score": 4, "comment": "基本到位"},
                            ],
                        },
                        {
                            "name": "内容",
                            "max_score": 20,
                            "score": 15,
                            "comment": "内容可再扩展",
                            "items": [
                                {"name": "论据", "max_score": 10, "score": 7, "comment": "论据略少"},
                                {"name": "逻辑", "max_score": 10, "score": 8, "comment": "逻辑基本清晰"},
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "file_name": "王五.docx",
            "student_id": "2025002",
            "student_name": "王五",
            "score": 88.0,
            "score_rubric": 44.0,
            "score_rubric_max": 50.0,
            "status": "成功",
            "error_message": None,
            "comment": "总体评语：论证充分，建议精简重复段落。",
            "detail_json": json.dumps({"score_target_max": 100.0}, ensure_ascii=False),
            "aggregate_strategy": "mean",
            "grader_results": [
                {
                    "model_index": 1,
                    "api_url": "http://a",
                    "model_name": "main",
                    "status": "成功",
                    "score": 88,
                    "comment": "主模型评语：亮点明显。",
                    "error_message": None,
                    "latency_ms": 90,
                    "sections": [],
                }
            ],
        },
    ]

    error_rows = [
        {
            "file_name": "李四.docx",
            "error_type": "解析校验错误",
            "error_message": "解析失败：" + ("很长的错误信息用于测试自动换行与行高自适应。" * 8),
        }
    ]

    out_path = exporter.export_results(
        rows,
        summary={"批次ID": "demo-batch", "生成时间": "now", "目标满分": 60.0},
        error_rows=error_rows,
    )
    err_path = exporter.export_errors(error_rows)
    print(f"成绩表：{out_path}")
    print(f"异常清单：{err_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
