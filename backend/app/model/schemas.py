"""
Pydantic 数据模型定义，描述接口输入输出结构。
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ModelEndpoint(BaseModel):
    """单个模型端点配置（支持多模型批改）。"""

    model_config = ConfigDict(protected_namespaces=())

    api_url: str = Field(..., description="大模型接口地址")
    api_key: Optional[str] = Field(None, description="大模型访问密钥")
    model_name: str = Field(..., description="模型名称")


class GradeConfig(BaseModel):
    """评分配置输入模型。"""

    api_url: Optional[str] = Field(None, description="大模型接口地址")
    api_key: Optional[str] = Field(None, description="大模型访问密钥")
    model_name: Optional[str] = Field(None, description="模型名称")
    models: Optional[List[ModelEndpoint]] = Field(None, description="追加模型端点配置（最多 2 个，不含默认模型）")
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
    aggregate_strategy: Optional[str] = None
    grader_results: Optional[list[dict]] = None


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


class RubricGenerateRequest(BaseModel):
    """评分标准生成请求。"""

    description: str = Field(..., description="老师对评分标准的文字描述", min_length=10)
    api_url: str = Field(..., description="大模型接口地址")
    api_key: Optional[str] = Field(None, description="大模型访问密钥")
    model_name: str = Field(..., description="模型名称")
    total_score: Optional[int] = Field(None, description="指定总分（可选，未指定时从描述中提取）")

    model_config = {"protected_namespaces": ()}


class RubricItem(BaseModel):
    """评分细则。"""

    key: str = Field(..., description="细则名称")
    max_score: float = Field(..., description="该细则满分（扣分项时为最大扣分额度）")
    description: str = Field(..., description="评分要求描述")
    is_deduction: bool = Field(False, description="是否为扣分项（true时分数为负，表示扣分）")


class RubricSection(BaseModel):
    """评分维度。"""

    key: str = Field(..., description="维度名称")
    max_score: float = Field(..., description="该维度满分")
    items: List[RubricItem] = Field(..., description="该维度下的评分细则")


class RubricGenerateResponse(BaseModel):
    """评分标准生成响应。"""

    category_key: str = Field(..., description="分类标识（英文下划线命名）")
    display_name: str = Field(..., description="分类显示名称")
    sections: List[RubricSection] = Field(..., description="评分维度列表")
    total_score: float = Field(..., description="总分")
