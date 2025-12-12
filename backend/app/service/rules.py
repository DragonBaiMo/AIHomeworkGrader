"""
评分规则与作业类型工具模块。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from config.settings import BASE_DIR
from app.service.prompt_builder import build_user_prompt
from app.service.prompt_config import load_prompt_config


AssignmentCategory = str


@dataclass(frozen=True)
class AssignmentRule:
    """单类作业的评分与校验规则。"""

    name: str
    min_length: int
    description: str


RULES: dict[AssignmentCategory, AssignmentRule] = {
    "career_plan": AssignmentRule(
        name="职业规划书",
        min_length=50,
        description=(
            "《职业规划书》需包含：个人情况剖析、职业选择分析、行业分析、岗位目标与实施计划等内容，"
            "重点考察自我认知是否清晰、职业目标是否具体可行、路径规划是否有步骤与时间节点。"
        ),
    ),
    "major_analysis": AssignmentRule(
        name="专业分析报告",
        min_length=50,
        description=(
            "《专业分析报告》需不少于2000字（正文主体部分），包含对行业发展情况分析、"
            "AI 对行业的正负面影响、学完本专业后可从事的岗位与薪资预期等，"
            "重点考察行业理解深度与逻辑分析能力。"
        ),
    ),
    "generic": AssignmentRule(
        name="通用写作",
        min_length=50,
        description="通用写作任务，仅要求结构清晰、论点明确、用语规范。",
    ),
}

PROMPT_FILE_PATH = BASE_DIR / "config" / "prompts.md"
_PROMPT_CACHE: Dict[str, str] = {}


def _load_prompts() -> Dict[str, str]:
    """从 Markdown 文件中加载提示词配置。"""
    global _PROMPT_CACHE
    if _PROMPT_CACHE:
        return _PROMPT_CACHE
    if not PROMPT_FILE_PATH.exists():
        _PROMPT_CACHE = {}
        return _PROMPT_CACHE

    prompts: Dict[str, str] = {}
    current_key: Optional[str] = None
    buffer: list[str] = []
    for line in PROMPT_FILE_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if current_key is not None:
                prompts[current_key] = "\n".join(buffer).strip()
                buffer = []
            current_key = line[3:].strip()
        else:
            if current_key is not None:
                buffer.append(line)
    if current_key is not None and buffer:
        prompts[current_key] = "\n".join(buffer).strip()

    _PROMPT_CACHE = prompts
    return _PROMPT_CACHE


def _normalize_label(label: str) -> str:
    """统一作业名称文案，便于判断类型。"""
    return label.replace(" ", "").replace("：", ":").strip()


def _is_auto_template_hint(template_hint: Optional[str]) -> bool:
    """判断模板提示是否代表“自动识别”。"""
    hint = _normalize_label(template_hint or "")
    if not hint:
        return True
    if hint == "auto":
        return True
    if hint.startswith("自动识别"):
        return True
    return hint in ("通用作业分类批改", "职业规划书与专业分析报告的自动分类")


def detect_assignment_category(filename: str, template_hint: Optional[str] = None) -> AssignmentCategory:
    """
    根据文件名中的关键字判断作业类型。

    规则：
    1. 文件名只要包含“职业规划书”或“职业规划”，则视为职业规划书；
    2. 文件名只要包含“专业分析报告”或“专业分析”，则视为专业分析报告；
    3. 若两类关键字同时出现，或两类关键字都未出现，则视为问题文件，抛出异常；
       由上层记录到异常清单中。
    """
    # 若前端明确选择了分类（低代码模式），优先使用选择结果。
    hint = _normalize_label(template_hint or "")
    config = load_prompt_config()
    if hint and not _is_auto_template_hint(hint):
        if config is not None:
            if hint in config.categories:
                return hint
            for cat_key, cat_cfg in config.categories.items():
                if _normalize_label(cat_cfg.display_name) == hint:
                    return cat_key
        raise ValueError(f"未找到对应作业分类：{template_hint}")

    text = _normalize_label(filename)
    if config is not None and config.categories:
        matched: list[tuple[str, str]] = []
        for cat_key, cat_cfg in config.categories.items():
            keyword = _normalize_label(cat_cfg.display_name or "")
            if keyword and keyword in text:
                matched.append((cat_key, cat_cfg.display_name))

        if len(matched) == 1:
            return matched[0][0]
        if not matched:
            raise ValueError("作业文件名未匹配到任何分类关键字，请检查文件名是否包含分类列表名称。")
        names = "、".join(name for _key, name in matched)
        raise ValueError(f"作业文件名同时命中多个分类关键字：{names}。请确保文件名仅包含一个分类关键字。")

    has_career = ("职业规划书" in text) or ("职业规划" in text)
    has_major = ("专业分析报告" in text) or ("专业分析" in text)

    if has_career and not has_major:
        return "career_plan"
    if has_major and not has_career:
        return "major_analysis"

    raise ValueError("作业文件命名无法唯一识别为“职业规划书”或“专业分析报告”，请检查命名格式。")


def get_rule(category: AssignmentCategory) -> AssignmentRule:
    """获取对应作业类型的规则配置。"""
    return RULES.get(category) or RULES["generic"]


def get_system_prompt() -> str:
    """获取系统级提示词，允许通过 Markdown 配置覆盖默认值。"""
    config = load_prompt_config()
    if config is not None:
        return config.system_prompt
    prompts = _load_prompts()
    custom = prompts.get("system")
    if custom:
        return custom
    return "你是一名严格的高校教师，负责批改学生作业。请严格按照要求只输出一个 JSON 对象，不要输出任何解释文字、不要使用 Markdown 代码块。"


def build_template_prompt(category: AssignmentCategory) -> str:
    """
    构造传入大模型的评分说明文案。

    约定大模型返回结构：
    {
        "score": 总分(float, 0-100),
        "comment": "总体评语",
        "dimension": {
            "structure": 结构与格式分(int),
            "content": 内容与分析深度分(int),
            "expression": 语言表达与逻辑分(int)
        },
        "model": "实际使用的模型名称"
    }
    """
    config = load_prompt_config()
    if config is not None:
        cat_cfg = config.categories.get(category)
        if cat_cfg is not None:
            # 注意：这里仅作为兜底旧逻辑使用；新逻辑在 grading_service 中会带入 score_target_max 编译。
            prompt, _expected = build_user_prompt(cat_cfg, score_target_max=60.0)
            return prompt

    prompts = _load_prompts()
    key = category
    custom = prompts.get(key)
    if custom:
        return custom

    rule = get_rule(category)
    if category == "career_plan":
        detail = (
            "1. 个人情况剖析（约20分）：能否对自身性格、能力、兴趣、价值观进行有逻辑的分析；"
            "2. 职业选择分析（约25分）：是否对目标职业进行充分了解与匹配说明；"
            "3. 行业分析（约20分）：是否对目标行业的发展现状与趋势做出分析；"
            "4. 岗位目标与实施计划（约25分）：是否给出清晰的阶段目标、时间安排与行动路径；"
            "5. 格式与规范（约10分）：结构是否完整、语句是否通顺、是否符合作业格式要求。"
        )
    elif category == "major_analysis":
        detail = (
            "1. 行业发展分析（约30分）：是否基于可信信息对行业现状与未来趋势做出系统性分析；"
            "2. AI 正负面影响（约30分）：是否能从多个角度分析 AI 技术对行业的积极与消极作用；"
            "3. 岗位与薪资认知（约20分）：是否结合本专业给出可从事岗位及合理薪资区间；"
            "4. 结构与论证（约10分）：全文结构是否清晰、论点与论据是否匹配；"
            "5. 表达与规范（约10分）：语言是否准确流畅、是否符合不少于 2000 字等形式要求。"
        )
    else:
        detail = (
            "1. 文章结构（约30分）：结构是否完整、段落衔接是否自然；"
            "2. 内容充实度（约40分）：论点是否明确、论据是否充分；"
            "3. 表达与规范（约30分）：语言是否准确、是否存在明显语病与格式问题。"
        )

    prompt = (
        f"你是一名高校教师，请根据以下评分要求批改学生的《{rule.name}》作业，满分 100 分。\n"
        f"【作业说明】{rule.description}\n"
        f"【评分维度与建议分值】{detail}\n"
        "【输出要求】你必须严格按照下面的 JSON 结构返回结果：\n"
        '{\n'
        '  "score": 85.5,\n'
        '  "comment": "总体评语，150 字以内的中文字符串",\n'
        '  "dimension": {\n'
        '    "structure": 88,\n'
        '    "content": 90,\n'
        '    "expression": 82\n'
        '  },\n'
        '  "model": "moonshotai/Kimi-K2-Thinking"\n'
        '}\n'
        "所有分数字段必须是 0-100 范围内的数值（整数或小数），不得为 null、空字符串或非数字。\n"
        "不要添加任何额外字段，不要输出说明文字，不要使用 Markdown 代码块，只输出一个 JSON 对象。"
    )
    return prompt
