官方文档链接：

```text
Gemini API Reference（含认证与 curl 示例，页面包含“Authentication”段落；版本：v1beta）
https://ai.google.dev/api
（页面内示例与说明：要求所有请求带 x-goog-api-key；含 generateContent curl 示例）:contentReference[oaicite:0]{index=0}

REST 方法：models.generateContent / models.streamGenerateContent（端点、请求体字段、响应结构；版本：v1beta）
https://ai.google.dev/api/rest/v1beta/GenerateContentResponse
（其中列出 generateContent 与 streamGenerateContent 端点与 Request body/Response body 结构）:contentReference[oaicite:1]{index=1}

内容结构：Content / Part / Blob / FileData（字段定义与 JSON 表示）
https://ai.google.dev/api/caching
（该参考页包含 Content/Part/Blob/FileData 的字段与 JSON representation）:contentReference[oaicite:2]{index=2}

Files API（概念说明：存储上限、单文件上限、保存时长）
https://ai.google.dev/gemini-api/docs/files
（每项目最多 20GB、单文件最大 2GB、文件保存 48 小时等）:contentReference[oaicite:3]{index=3}

Files REST：files.list 等方法（端点示例；版本：v1beta）
https://ai.google.dev/api/files
（例如 files.list 端点：GET https://generativelanguage.googleapis.com/v1beta/files） :contentReference[oaicite:4]{index=4}

API 版本说明（v1 vs v1beta）
https://ai.google.dev/gemini-api/docs/api-versions
（解释 v1beta 可能发生破坏性变更，v1 更稳定）:contentReference[oaicite:5]{index=5}

GenerationConfig（输出长度等生成参数字段的定义）
https://ai.google.dev/api/rest/v1beta/GenerationConfig
:contentReference[oaicite:6]{index=6}

API Key 文档（也给出 REST Header：x-goog-api-key）
https://ai.google.dev/gemini-api/docs/api-key
:contentReference[oaicite:7]{index=7}
```

认证方式：

1. API Key（最常用）：所有请求必须在 Header 里带 `x-goog-api-key: <YOUR_API_KEY>`。([Google AI for Developers][1])
2. 还需要 `Content-Type: application/json`（JSON 请求）。官方 curl 示例就是这么写的。([Google AI for Developers][1])

端点与方法：

1. 标准生成（一次性返回完整结果）

* POST `https://generativelanguage.googleapis.com/v1beta/{model=models/*}:generateContent` ([Google AI for Developers][2])

2. 流式生成（SSE 分段返回）

* POST `https://generativelanguage.googleapis.com/v1beta/{model=models/*}:streamGenerateContent` ([Google AI for Developers][2])
* 成功时返回的是一串 `GenerateContentResponse` 实例流。([Google AI for Developers][2])

3. Files（用于“先上传、再引用”那条路）

* GET `https://generativelanguage.googleapis.com/v1beta/files`（files.list） ([Google AI for Developers][3])

请求结构（字段表）：

A) GenerateContentRequest（请求体顶层）([Google AI for Developers][2])
字段 | 类型 | 必填 | 说明

* contents | `Content[]` | 是 | 当前对话内容；单轮为 1 条，多轮则把历史都塞进去
* tools | `Tool[]` | 否 | 让模型可用的工具列表
* toolConfig | `ToolConfig` | 否 | 工具配置
* safetySettings | `SafetySetting[]` | 否 | 安全阈值设置（会作用于请求与候选输出）

B) Content（对话一轮消息）([Google AI for Developers][4])
字段 | 类型 | 必填 | 说明

* parts | `Part[]` | 是 | 一个消息由多个 Part 组成（文本/图片/音频/视频等混排）
* role | `string` | 否 | 生产者：`user` 或 `model`（多轮时建议写清楚）

C) Part（多模态载体，注意它是“联合类型”，一次只放一种 data）([Google AI for Developers][4])
字段 | 类型 | 必填 | 说明

* text | `string` | 否 | 文本
* inlineData | `Blob` | 否 | 内联媒体字节（base64）
* fileData | `FileData` | 否 | 引用一个 URI 指向的媒体
* （以及 functionCall/functionResponse 等，这里和多模态无关就不展开了）([Google AI for Developers][4])

D) Blob（inlineData 的结构）([Google AI for Developers][4])
字段 | 类型 | 必填 | 说明

* mimeType | `string` | 是 | IANA MIME（如 `audio/mpeg`, `video/mp4`, `image/jpeg`）
* data | `string(bytes)` | 是 | base64 编码后的原始字节

E) FileData（fileData 的结构）([Google AI for Developers][4])
字段 | 类型 | 必填 | 说明

* mimeType | `string` | 否 | IANA MIME（建议提供）
* fileUri | `string` | 是 | URI（引用上传后的文件）

重要但很人类的一点：字段命名在官方页面里会出现两种写法：

* curl 示例里常见 `inline_data / mime_type / file_uri` 这种 snake_case。([Google AI for Developers][1])
* 结构定义页里给的是 `inlineData / mimeType / fileUri` 这种 camelCase（protobuf/JSON 表示）。([Google AI for Developers][4])
  如果你是直接照官方 curl 抄，优先按 curl 示例的命名来，不要自作聪明发明第三种拼写。

成功响应示例：

1. 最小可用请求示例（REST，文本 + 音频 inline 上传）

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{
    "contents": [{
      "role": "user",
      "parts": [
        { "text": "请把这段音频转写成中文，并给出 3 条要点总结。" },
        {
          "inline_data": {
            "mime_type": "audio/mpeg",
            "data": "'"$(base64 -w 0 ./sample.mp3)"'"
          }
        }
      ]
    }]
  }'
```

* 端点与 Header（x-goog-api-key）是官方明确要求的。([Google AI for Developers][2])
* `contents[]` 必填，`role/parts` 的结构来自 Content/Part 定义。([Google AI for Developers][2])
* `inline_data` 的语义就是把媒体字节 base64 塞进请求。Blob 定义就是 `mimeType + data`。([Google AI for Developers][4])

2. 成功响应 JSON 示例（符合 GenerateContentResponse 结构）

```json
{
  "candidates": [
    {
      "index": 0,
      "content": {
        "role": "model",
        "parts": [
          { "text": "【转写】……\n\n【要点】1) … 2) … 3) …" }
        ]
      },
      "finishReason": "STOP",
      "safetyRatings": [
        { "category": "HARM_CATEGORY_HARASSMENT", "probability": "NEGLIGIBLE" }
      ]
    }
  ],
  "promptFeedback": {
    "safetyRatings": [
      { "category": "HARM_CATEGORY_HARASSMENT", "probability": "NEGLIGIBLE" }
    ]
  },
  "usageMetadata": {
    "promptTokenCount": 123,
    "candidatesTokenCount": 456,
    "totalTokenCount": 579
  },
  "modelVersion": "gemini-2.5-flash",
  "responseId": "abc123"
}
```

逐字段说明（官方语义对齐）：

* candidates：候选答案数组；模型可以返回多个候选。字段定义在 `GenerateContentResponse`：`candidates[]`。([Google AI for Developers][2])
* candidates[i].content：一个候选的“消息内容”，类型就是 `Content`；`Content.parts[]` 里放 `Part`。([Google AI for Developers][4])
* candidates[i].content.parts[j].text：当模型输出文本时，文本就在某个 Part 的 `text`。`Part` 的联合类型里明确包含 `text`。([Google AI for Developers][4])
* safety（两处）：

  * promptFeedback：提示词层面的过滤反馈；若提示被拦截，会有 `blockReason` 且不会返回任何 candidates。([Google AI for Developers][2])
  * candidates[i].safetyRatings + finishReason：对每个候选的过滤与结果进行报告。官方明确“提示与候选都会报告安全信息”。([Google AI for Developers][2])
* usageMetadata：本次请求的 token 用量元数据，属于响应顶层字段。([Google AI for Developers][2])
* modelVersion / responseId：响应顶层字段，用于标识本次生成使用的模型版本与响应 ID。([Google AI for Developers][2])

失败响应示例：

失败响应 JSON 示例（Google 标准 error 包装，Gemini API 也按这个套路来折腾你）

```json
{
  "error": {
    "code": 400,
    "message": "Invalid argument: unsupported mime type",
    "status": "INVALID_ARGUMENT",
    "details": [
      {
        "@type": "type.googleapis.com/google.rpc.BadRequest",
        "fieldViolations": [
          { "field": "contents[0].parts[1].inline_data.mime_type", "description": "Unsupported MIME type" }
        ]
      }
    ]
  }
}
```

常见错误码 / 错误字段（实战里最常见的那几类）：

* 400 `INVALID_ARGUMENT`：请求体字段不对、MIME 不支持、parts 结构不合法（比如一个 Part 同时塞 text 和 inlineData）。Part 是联合类型，官方写得很清楚“一次只能是其中一种”。([Google AI for Developers][4])
* 401/403：API Key 缺失、无效、或项目权限/配额相关（最经典的就是你以为你配好了 key，其实没有）。认证要求必须带 `x-goog-api-key`。([Google AI for Developers][1])
* 429：资源/配额耗尽（常见于限流或额度不足）。
  （更完整的排查路径在官方 Troubleshooting/指南里，一般就是围绕 code/message/status 看哪里写错。）

上传流程说明：

你有两条路，选你能忍的那条：

1. 不单独上传（inlineData 直接内联）

* 做法：把音频/图片/视频读成 bytes → base64 → 放到 `Part.inlineData`（curl 示例中写作 `inline_data`）里。([Google AI for Developers][4])
* 优点：一次请求搞定，最“最小可用”。
* 代价：请求体会膨胀；大文件会让你和各种网关/限制正面硬刚。

2. 先用 Files API 上传，再在生成请求中引用（fileData）

* Files API 的定位：上传并“暂存”媒体文件；官方说明每项目最多 20GB、单文件最大 2GB、文件保存 48 小时。([Google AI for Developers][5])
* 上传后你会拿到可引用的 `fileUri`（概念上就是“这个文件的 URI”），然后在生成请求里用 `Part.fileData.fileUri` 引用它。`FileData.fileUri` 是必填字段。([Google AI for Developers][4])
* Files REST 至少明确了列表端点（`GET /v1beta/files`），用于查看你已有的文件与元数据。([Google AI for Developers][3])

截断/限制说明：

1. 输出长度限制（截断最常见原因）

* 生成相关的限制是通过 `GenerationConfig` 这类生成参数控制的（例如最大输出 token 数等）。([Google AI for Developers][6])
* 当达到限制时，响应会通过候选的结束原因等字段回报生成为何停止（例如正常停止、被安全策略拦截、达到长度上限等）。官方明确候选会在 `finishReason` 与 `safetyRatings` 中报告过滤与结束情况。([Google AI for Developers][2])

2. 分段/流式返回（避免“等半天才吐一坨”）

* `streamGenerateContent` 会返回一串 `GenerateContentResponse` 分段（SSE），官方写明“响应体是一个 GenerateContentResponse 流”。([Google AI for Developers][2])

3. “为空/没有 candidates”的官方情况

* 官方明确：如果提示词被拦截（`promptFeedback.blockReason`），不会返回任何 candidates；并且“只有提示本身有问题时才会返回 0 candidates，需检查 promptFeedback”。([Google AI for Developers][2])

如果你接下来要我把上面内容进一步收敛成“Node/TS 的最小可用代码（含读取音频、base64、错误处理、重试、流式 SSE 解析）”或要我锁定某个具体模型名（比如你举的 `gemini-flash-latest`），我才需要按你的目标再定一版“精确到模型与 SDK”的实现细节。

[1]: https://ai.google.dev/api "Gemini API reference  |  Google AI for Developers"
[2]: https://ai.google.dev/api/rest/v1beta/GenerateContentResponse "Generating content  |  Gemini API  |  Google AI for Developers"
[3]: https://ai.google.dev/api/files?utm_source=chatgpt.com "Using files | Gemini API - Google AI for Developers"
[4]: https://ai.google.dev/api/caching "Caching  |  Gemini API  |  Google AI for Developers"
[5]: https://ai.google.dev/gemini-api/docs/files?utm_source=chatgpt.com "Files API | Gemini API - Google AI for Developers"
[6]: https://ai.google.dev/api/rest/v1beta/GenerationConfig "Generating content  |  Gemini API  |  Google AI for Developers"
