你是一个资深 Python 工程师，正在修改一个项目里的 Excel 导出模块 `excel_utils.py`（openpyxl）。目标是：**保持原业务逻辑完全不变**（数据计算/字段含义/维度&细则展开方式不改），但把导出的 Excel **美观性、结构、筛选、空行分隔**做到与用户提供的示例模板 `示例_作业批改报表.xlsx` 尽可能一致。

### 你必须遵守的硬约束

1. **业务逻辑不变**：

   * `export_results(rows, summary=None, error_rows=None)` 的输入/输出、字段来源、计算方式（均值、极差、模型成功/失败数等）保持不变
   * `export_errors(rows)` 保持可用（可以也用模板，但功能不要缩水）
2. **输出 Excel 的“视觉风格”以模板为准**：

   * 不要用“手工 fill/border 堆样式”来试图复刻美观
   * 必须采用“**模板法**”：加载模板 xlsx，清空示例数据，再填入真实数据，并扩展模板里 Excel Table 的 `ref`
3. **筛选必须存在**：

   * 筛选依赖 Excel Table（`openpyxl.worksheet.table.Table`），不是 `sheet.auto_filter`
   * 你必须保证每个核心表都保持 Table，并在填数据后正确更新 `table.ref` 范围到最后一行
4. **多个文件/学生之间必须空一行分隔**：

   * 为可读性，每个 file/student 的数据块后插入一行空行（`[None]*N`）
   * 但空行必须仍在 Table 范围内，确保筛选不“断”
5. **条件格式、图表、Dashboard 布局尽量保留模板现有**

   * 不要重建图表，不要删除模板的条件格式规则
   * 只需确保数据源范围可用（必要时让模板图表引用一个固定的“数据”sheet并覆盖其值）

### 模板文件

项目中放置模板文件：`app/assets/grade_template.xlsx`（你可假设此路径存在；若不存在，说明如何配置）

模板内工作表（示例）：

* `Dashboard`（含 KPI 卡片/图表/摘要）
* `数据`（Dashboard 图表的数据源）
* `成绩总览`
* `模型结果（长表）`
* `批改模型结果（宽表）`
* `维度汇总`
* `细则明细`
* `批次总览`
* `错误统计`
* `错误明细`（若模板没有，可保留项目原 “错误” sheet）

模板内 Table 名称（示例，需通过代码实际读取/匹配）：

* 成绩总览：`OverviewTbl`
* 模型长表：`ModelLong`
* 模型宽表：`ModelWide`
* 维度汇总：`DimSummary`
* 细则明细：`RubricDetail`
* 批次总览：`BatchSummary`
* 错误统计：`ErrStats`
* 错误明细：`ErrDetail`（如存在）

> 重要：不要硬编码 `ref`，而是“读取模板已有 table 对象 → 填数据 → 更新它的 ref”。

---

## 实现方案（必须照做）

### 1) 修改 export_results：从 Workbook() 变为 load_workbook(template)

* 使用：`openpyxl.load_workbook(template_path)`
* 不要新建 Workbook，不要重建所有 sheet
* 从模板取到对应的 worksheet

### 2) 清空模板中的示例数据，但保留：标题/表头/表格/Table/条件格式/图表

对每个表：

* 找到该表的 Table（例如 `ws.tables`）
* Table.ref 形如 `"A4:M28"`，其中 `start_row` 是表头行（header_row）
* 清空方式：

  * **保留 header_row 不动**
  * 删除 header_row 之后的数据行（直到原 ref 的末行），或把单元格 value 置空
  * 注意不要破坏合并单元格、不要删除图表、不要删除条件格式

推荐：把 table 数据区（header_row+1 到 old_max_row）逐格 `.value=None`（不要 delete_rows，避免图表/引用错位）

### 3) 填充数据：严格按模板列顺序写入

#### 成绩总览（示例列可能为）

* 状态、最终分、姓名、学号、文件名、模型通过率、总体评语、错误描述、查看模型、查看细则、（可隐藏工程列：规则得分/满分/聚合算法/成功失败模型数等）
  要求：
* “查看模型/查看细则”要填入 `HYPERLINK("#'模型结果（长表）'!A{row}","查看模型")` 这类公式
* 需要你在填“模型长表”和“细则明细”时记录每个 student/file 的首行行号，用来生成跳转

#### 模型结果（长表）

每个模型一行：文件名/学号/姓名/模型/状态/分数/耗时/评语/（可选采用标识）

* 行号映射：`model_row_map[file_key]=first_row`

#### 批改模型结果（宽表）

维持原业务逻辑的宽表输出（每个模型 5 列一组）

#### 维度汇总/细则明细

* 维度汇总：按维度名称对齐，输出成功模型均值、满分、各模型得分、极差、维度评语
* 细则明细：按细则名称对齐，输出成功模型均值、满分、各模型得分、极差、扣分原因
* 每个文件结束插入空行（仍在 Table 范围内）

#### 批次总览

把 summary 的 key/value 写入模板对应区域（保留模板样式），必要时扩展 Table.ref

#### 错误统计/错误明细

* error_rows 为空则仍保留表头
* 错误统计按 error_type 聚合计数
* 错误明细写入 file_name/error_type/error_message
* 都要扩展 table.ref

### 4) “空一行分隔”但筛选不断：关键技巧

* 每写完一个 file/student 块，在该 sheet append 一行 `[None]*N`
* 最后更新 Table.ref 覆盖到包含空行的最后一行

### 5) 更新 Table.ref（非常关键）

实现工具函数：`_resize_table(ws, table_name_or_first, header_row, last_row, last_col)`

* last_col 来自模板 table.ref 的 max_col（不要因为数据多就扩展列，列数固定遵循模板）
* 例：`table.ref = f"{min_col_letter}{header_row}:{max_col_letter}{last_row}"`

### 6) 仍保留 sheet.auto_filter（可选）

即使有 Table，auto_filter 可不设。但如果模板没有 Table 的筛选按钮，才 fallback 用 auto_filter。优先 Table。

### 7) 保留条件格式 / 图表

* 不要删除 `ws.conditional_formatting`
* Dashboard 图表若引用 `数据` sheet，你只需覆盖 `数据` sheet 指定区域（如分布桶、成功失败数、维度均分等）
* 不要改图表对象

### 8) 输出文件命名与路径不变

* `grade_result.xlsx` 存到 `batch_dir` 下

---

## 验收标准（必须通过）

1. 打开导出的 `grade_result.xlsx`：

   * 每个 sheet 的表头样式、斑马纹、字体/颜色与模板一致
   * 表头有筛选下拉箭头（Table 生效）
2. “多个文件空一行”可见，并且筛选仍覆盖全部数据（包含空行）
3. “查看模型/查看细则”点击能跳转到对应 sheet 的正确位置
4. 维度/细则的均值、极差等数值与原逻辑输出一致（可对比旧版导出）
5. Dashboard 不被破坏（至少不报错、布局在）

---

## 你需要在代码里做的具体改动点

* 在 `excel_utils.py` 顶部新增：`from openpyxl import load_workbook`
* 在 `ExcelExporter.__init__` 加模板路径：`self.template_path = Path(__file__).resolve().parent / "assets" / "grade_template.xlsx"`（或按项目结构）
* 重写 `export_results` 使其：

  1. load 模板
  2. 获取 sheets
  3. 清空表格数据区
  4. 写入数据（保持原算法）
  5. 插入分隔空行
  6. 更新每个 table.ref
  7. save
* 可保留你原来的样式函数但不要再用于主导美观（模板自带）

---

## 额外注意事项

* openpyxl 对图表引用很敏感：尽量“清空 value”，不要 `delete_rows`
* 合并单元格区域不要拆
* Table `displayName` 不能变（Excel 要求唯一，且模板里已定义）
* `sheet.max_row` 在合并单元格时可能不直观，用 table.ref 推导 header_row 更稳