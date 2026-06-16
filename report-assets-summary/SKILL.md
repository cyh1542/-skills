---
name: report-assets-summary
description: >-
  根据巡检报告目录下 charts/（PNG 图）与 tables/（CSV 明细）自动归纳总结，
  保存为 Markdown（summary.md）与结构化 CSV（summary.csv）。
  适用于周报后处理、总结 charts 和 tables、生成 summary.csv、读取 report 输出目录。
---

# 巡检结果总结 (report_assets_summary)

## 适用场景

- `weekly-ops-report` 或其它分析流程已产出 `charts/`、`tables/`，需要**二次总结**成可读结论
- 用户要求「根据 charts 和 tables 文件夹总结」「生成 summary」「归纳图表和 CSV」
- 不想重新跑全量分析，仅基于**已有交付物**写摘要

## 输入

| 参数 | 说明 |
|------|------|
| `report_dir` | 报告根目录，须包含子目录 `charts/` 和/或 `tables/` |
| `--md` | 可选，默认 `summary.md` |
| `--csv` | 可选，默认 `summary.csv`（**必选交付**，结构化总结） |

示例路径：

```text
D:\python_program\data\reports\weekly_20180830\
├── charts\*.png
├── tables\*.csv
├── summary.md          ← 可读报告
└── summary.csv         ← 结构化总结（单独 CSV，必选）
```

### summary.csv 列说明

| 列名 | 说明 |
|------|------|
| 类别 | 执行摘要 / 数据明细 / 图表解读 / 行动建议 / 元信息 |
| 子类 | 履约、体验、卖家延迟、差评归因等 |
| 指标名称 | 如「本周延迟率」「延迟率」 |
| 指标值 | 数值或百分比文本 |
| 对象ID | 卖家ID、品类名、分箱名、图表名等 |
| 说明 | 补充解释 |
| 数据来源 | 对应 tables/*.csv 或 charts/*.png |
| 优先级 | 高 / 中 / 低 |
| 需人工确认 | 是 / 否 |

## 工具

| 工具 | 用途 |
|------|------|
| `scripts/summarize_report_assets.py` | 读取全部 CSV、嵌入图表、按表类型生成要点 |
| Read（图片） | 对关键 PNG 做视觉补充（趋势方向、峰值等） |
| Write | 将 Agent 补充后的最终版写入 `summary.md` |
| `scripts/export_report_docx.py` | 导出 Word（`.docx`），嵌入图表与表格 |
| `scripts/create_word_template.py` | 生成/更新 Word 模板骨架 |
| python-docx | Word 读写依赖（`pip install python-docx`） |

## 执行流程

### 1. 校验目录

确认 `report_dir` 存在，且至少其一非空：

- `tables/*.csv`
- `charts/*.png`

若两者皆空，中止并提示先运行 `weekly-ops-report`。

### 2. 运行脚本（生成 MD + CSV）

```bash
python .cursor/skills/report-assets-summary/scripts/summarize_report_assets.py "<report_dir>"
```

同时指定输出文件名：

```bash
python .cursor/skills/report-assets-summary/scripts/summarize_report_assets.py "<report_dir>" --md summary.md --csv summary.csv
```

脚本会：

1. 扫描 `tables/*.csv`，提取指标写入 **`summary.csv`**（每行一条总结项）
2. 扫描 `charts/*.png`，在 CSV「图表解读」类与 Markdown 中登记
3. 写入 `summary.md`（可读版，并引用 summary.csv）

### 3. Agent 增强（推荐）

脚本无法代替人眼读图。对 `charts/` 中每张 PNG：

1. 使用 **Read** 打开图片
2. 用 1–2 句话补充**视觉结论**（如「近 8 周延迟率先降后升」「延迟>7 天分箱差评率明显跳升」）
3. 将补充文字写入 `summary.md` 对应「图表解读」小节，替换占位提示

### 4. 交叉核对

- 文字结论须与 CSV 数值一致（延迟率、差评率、风险分等）
- 若 `report.md` 同目录存在，可与之一致性比对，但不覆盖 `report.md`

### 5. 导出 Word（可选）

先生成模板（首次或更新版式时）：

```bash
python .cursor/skills/report-assets-summary/scripts/create_word_template.py
```

导出 Word 报告（默认使用 `templates/weekly_inspection_report_template.docx` 的版式）：

```bash
python .cursor/skills/report-assets-summary/scripts/export_report_docx.py "<report_dir>"
```

指定输出路径：

```bash
python .cursor/skills/report-assets-summary/scripts/export_report_docx.py "<report_dir>" -o "<report_dir>/inspection_report.docx"
```

## 输出

| 文件 | 必须 | 说明 |
|------|------|------|
| `summary.csv` | **是** | 结构化总结，可导入 Excel / BI |
| `summary.md` | 推荐 | 图文可读版 |
| `*_report.docx` | 可选 | Word 报告（含图表嵌入、明细表、行动建议） |
| `templates/weekly_inspection_report_template.docx` | 可选 | Word 版式模板骨架 |
| `../Olist_Skills_工具清单与输入输出定义.docx` | 参考 | 全部 Skill 工具与 I/O 定义（`scripts/export_skills_catalog_docx.py` 生成） |

## 输出结构模板

`summary.md` 结构：

```markdown
# 巡检结果总结 | weekly_YYYYMMDD

## 执行摘要
- （3–5 条要点）

## 图表解读
### delay_trend
![...](charts/delay_trend.png)
**说明**：...
（Agent 视觉补充）

## 数据明细摘要
### seller_risk_list
- 要点
| 表格 |

## 行动建议（待人工确认）
```

## 支持的 tables 文件（自动识别）

| 文件名 | 总结内容 |
|--------|----------|
| weekly_delay_trend.csv | 周延迟率环比 |
| seller_risk_list.csv | 高风险卖家数量与 TOP |
| problem_categories.csv | 问题品类与优先级 |
| delay_by_seller.csv | 高延迟卖家 |
| delay_by_category.csv | 高延迟品类 |
| delay_by_region.csv | 高延迟区域 |
| review_by_delay_bins.csv | 延迟与差评关系 |
| 其它 CSV | 行数 + 前 10 行预览 |

## 支持的 charts 文件（自动图说）

| 文件名 | 默认说明 |
|--------|----------|
| delay_trend.png | 延迟率周趋势 |
| delay_top_sellers.png | 卖家延迟 TOP |
| bad_review_by_delay_bins.png | 延迟分箱 vs 差评率 |
| seller_risk_scatter.png | 卖家风险散点 |

## 失败条件（中止）

- `report_dir` 不存在
- `charts/` 与 `tables/` 均无有效文件
- CSV 编码无法读取（改用 `utf-8-sig` 重试）

## 人工接管点

- 总结中的**处罚/下架/赔偿**建议仅作参考，标注「待人工确认」
- 图表视觉描述与 CSV 冲突时，以 CSV 为准并标注需复核

## 关联 skill

- 上游产出：[weekly-ops-report](../weekly-ops-report/SKILL.md)
- 数据口径：[olist-data-reference](../olist-data-reference/reference.md)
