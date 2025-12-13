"""
Pydantic 数据模型定义，描述接口输入输出结构。
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GradeConfig(BaseModel):
    """评分配置输入模型。"""

    api_url: Optional[str] = Field(None, description="大模型接口地址")
    api_key: Optional[str] = Field(None, description="大模型访问密钥")
    model_name: Optional[str] = Field(None, description="模型名称")
    template: str = Field("职业规划书与专业分析报告的自动分类", description="评分模版或作业类型提示")
    mock: bool = Field(False, description="是否启用离线模拟评分")
    skip_format_check: bool = Field(False, description="是否跳过文档格式校验（仅对 docx 生效）")
    score_target_max: float = Field(60.0, description="目标满分（用于将评分规则总分按比例换算）")

    model_config = {"protected_namespaces": ()}


class FileBrief(BaseModel):
    """单个文件的基础信息。"""

    file_name: str
    student_id: Optional[str]
    student_name: Optional[str]


class GradeItem(BaseModel):
    """单个作业的评分结果。"""

    file_name: str
    student_id: Optional[str]
    student_name: Optional[str]
    score: Optional[float]
    score_rubric_max: Optional[float]
    score_rubric: Optional[float]
    detail_json: Optional[str]
    comment: Optional[str]
    status: str
    error_message: Optional[str]
    raw_text_length: int
    raw_response: Optional[str] = None


class GradeResponse(BaseModel):
    """批次评分返回结构。"""

    batch_id: str
    total_files: int
    success_count: int
    error_count: int
    average_score: Optional[float]
    download_result_url: str
    download_error_url: str
    items: List[GradeItem]
