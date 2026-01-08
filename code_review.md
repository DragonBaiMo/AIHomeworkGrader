# 变更摘要：实现流式批改（SSE）功能，包含后端流式接口、Service 层重构及前端进度条与取消支持。

整体实现逻辑清晰，Service 层的重构（提取 `_grade_single_file`）有效地复用了核心逻辑。流式处理中对文件句柄的生命周期管理（先保存后处理）考虑周全。

## 文件：backend/app/model/schemas.py
### L11-12：[MEDIUM] 全局禁用 Pydantic 警告风险
使用 `warnings.filterwarnings` 全局禁用 `protected_namespaces` 警告过于粗暴，可能会掩盖其他合法警告。
**建议**：在 `ModelEndpoint` 类中通过 `model_config` 局部禁用该检查，并移除全局副作用代码。

```diff
  from typing import List, Optional
 
- from pydantic import BaseModel, Field
+ from pydantic import BaseModel, Field, ConfigDict
 
- # 全局禁用 Pydantic 的 protected_namespaces 警告
- warnings.filterwarnings("ignore", message="Field.*has conflict with protected namespace")
 
 
  class ModelEndpoint(BaseModel):
      """单个模型端点配置（支持多模型批改）。"""
+     model_config = ConfigDict(protected_namespaces=())
 
      api_url: str = Field(..., description="大模型接口地址")
```

## 文件：backend/app/api/routes.py
### L111：[MEDIUM] 参数校验逻辑严重重复
`grade_stream` 接口复制了 `grade` 接口中约 50 行的参数校验与模型解析逻辑（JSON 解析、URL 校验等）。这违反了 DRY 原则，未来修改校验规则时极易导致两边行为不一致。
**建议**：将模型配置解析与校验逻辑提取为独立的依赖注入函数（Dependency）或工具函数，供两个接口共用。

```python
# 示例建议（伪代码）
def parse_and_validate_models(models_json: str | None, is_mock: bool) -> list[ModelEndpoint] | None:
    # ... 统一的解析逻辑 ...
    return parsed_models
```

## 文件：frontend/src/app/controller.ts
### L299-317：[LOW] 遗留调试日志
在 `onInit`, `onProgress`, `onItem` 等回调中保留了 `console.log`。生产环境代码应清除调试日志。
**建议**：移除或封装这些日志输出。

## 文件：backend/app/service/grading_service.py
### L306：[LOW] 异常处理后的数据一致性
在 `_grade_single_file` 中，当 `model_results` 全部失败时，构造的 `GradeItem` 返回了 `score=None`。但在 `process_stream_from_saved` 中导出 Excel 时，如果 `score` 为 None，可能会影响统计计算（虽然代码中有 `if score is not None` 检查）。
**确认**：确保 `ExcelExporter` 能正确处理 `score=None` 的情况，避免报表生成崩溃。从代码看 `average_score` 计算已经做了过滤，应该是安全的，但值得回归测试验证。
