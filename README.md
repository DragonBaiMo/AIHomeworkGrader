# AI 作业批改 Web 工具

本项目提供本地运行的 Python + FastAPI Web 服务，支持批量上传 `.docx` 作业、调用大模型生成分数与评语，并导出成绩表与异常清单。系统面向单机、单用户场景，强调“能用、清晰、易扩展”。

## 功能概览

- 多文件上传：一次选择多份 Word 作业，自动分批保存。
- 内容解析：校验 docx 格式，解析正文文本并做长度检查。
- 大模型评分：支持填写 API URL / API Key / 模型名称与评分模版，可切换离线模拟模式。
- 结果导出：生成成绩表（grade_result.xlsx）与异常清单（error_list.xlsx）。
- 页面体验：展示处理状态、批次统计，提供下载链接并记忆上次配置。

## 环境与依赖

- Python 3.11+
- 主要依赖：FastAPI、Uvicorn、python-docx、openpyxl、httpx、pydantic、pytest
- 完整依赖见 `requirements.txt`

## 安装步骤

1. 克隆或下载源码。
2. 创建虚拟环境并安装依赖：
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows 使用 .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```
3. 确认 `data/` 目录可写（程序启动时会自动创建）。

## 启动与使用

1. 启动后端服务：
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. 打开浏览器访问 [http://127.0.0.1:8000](http://127.0.0.1:8000)。
3. 页面步骤：
   - 选择一批 `.docx` 文件。
   - 填写模型接口信息（或勾选“离线模拟评分”）。
   - 选择评分模版，点击“开始批改”。
   - 等待完成后下载“成绩表”和“异常清单”。

### 接口说明

- 健康检查：`GET /api/ping`
- 触发批改：`POST /api/grade`
  - form-data 字段：`files`（多文件）、`api_url`、`api_key`、`model_name`、`template`、`mock`
- 下载结果：`GET /api/download/result/{batch_id}`
- 下载异常：`GET /api/download/error/{batch_id}`

## 目录结构

```
app/
  api/           # 接口路由
  service/       # 业务服务与模型调用
  util/          # 工具与日志
  model/         # Pydantic 数据模型
  static/        # 前端静态资源
config/          # 配置与路径定义
data/uploads/   # 批次文件与导出结果
```

## 测试

```bash
pytest
```

## 版本记录

- v0.1.0：完成批量上传、docx 解析、模型调用封装、Excel 导出与前端页面。

## 许可证

本项目采用 MIT License，详见仓库内 LICENSE 文件（若缺失请按需补充）。
