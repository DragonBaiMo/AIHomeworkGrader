# AI 作业批改前后端分离版

基于 **FastAPI + Vue3** 的本地作业批改工具，支持批量上传 `.docx`、调用大模型评分并导出成绩表/异常清单。前端使用 Vite 打包后静态托管在后端，亦可独立开发调试。

## 目录结构

```
backend/              # Python 后端
  app/                # FastAPI 业务代码
  config/             # 配置、提示词 JSON/Markdown
  data/               # 运行数据（上传文件、日志）
  tests/              # 后端单测
  requirements.txt    # 后端依赖
frontend/             # Vue3 前端（Vite）
  src/                # 业务代码与样式
  vite.config.ts      # 打包到 backend/app/static
  package.json        # 前端依赖
.venv/                # Python 虚拟环境（脚本自动创建）
start.bat             # 一键启动后端（含静态资源）
reset-env.bat         # 重置 Python 虚拟环境并安装依赖
```

## 快速开始

1) 初始化后端环境（根目录执行）：
```bat
reset-env.bat
```

2) 启动后端并托管已构建的前端（默认端口 18088）：
```bat
start.bat
```
访问 `http://localhost:18088` 查看页面，`/docs` 为 OpenAPI 文档。

## 前端开发

```bat
cd frontend
npm install          # 首次安装依赖
npm run dev -- --host  # 启动 Vite 开发服务器（端口 5173，已代理 /api -> 8000）
npm run build          # 打包，产物输出到 backend/app/static
```

## 后端开发

```bat
cd backend
..\ .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 18088
```

- 健康检查：`GET /health` 或 `GET /api/ping`
- 批改接口：`POST /api/grade`（表单字段：files、api_url、api_key、model_name、template、mock、skip_format_check）
- 下载结果：`GET /api/download/result/{batch_id}`
- 下载异常：`GET /api/download/error/{batch_id}`
- 提示词配置：`GET/POST /api/prompt-config`

## 数据与日志

- 上传与导出文件位于 `backend/data/uploads`，默认会生成批次号目录。
- 运行日志位于 `backend/data/logs/runtime.log`。
- 默认提示词配置存放于 `backend/config/prompt_config.json`，保存后会同步生成 `prompts.md`。
- 成绩表 `grade_result.xlsx` 会包含“按学号汇总”工作表（列：学号｜学生｜总成绩｜目标成绩｜总评分），并按学号升序排列（学号缺失的记录排在最后）；其中“目标成绩”优先取该学生记录 `detail_json.score_target_max`，缺失时回退到批次总览的“目标满分”。

## 注意事项

- 所有前后端文案、日志与注释均为中文，严禁中英夹杂。
- 前端配置（接口地址、Key 等）保存在浏览器 `localStorage`，后端不持久化敏感信息。
- 生产环境请自行添加身份验证与更严格的权限/输入校验。前端提供的「离线模拟模式」可在无模型接口时演示流程。  
