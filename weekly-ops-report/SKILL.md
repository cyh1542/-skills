---
name: weekly-ops-report
description: >-
  基于 Olist 巴西电商多表数据自动生成经营巡检周报：订单履约、延迟、差评、卖家风险、品类体验。
  输出 Markdown 报告、图表 PNG 与明细表。适用于每周例会、经营巡检、Olist 数据分析、周报生成。
---

# 经营巡检周报 (weekly_ops_report)

## 适用场景

- 每周经营例会前，需要一份可重复生成的订单履约与客户体验分析
- 用户询问「近一周经营情况」「履约是否恶化」「生成巡检周报」
- 需要同时交付**文字结论 + 数据表 + 图表**（非纯 BI 看板）

## 输入

数据目录路径，包含以下 CSV（文件名可含 `olist_` 前缀）：

| 逻辑名 | 数据集 |
|--------|--------|
| orders | olist_orders_dataset |
| order_items | olist_order_items_dataset |
| payments | olist_order_payments_dataset |
| reviews | olist_order_reviews_dataset |
| products | olist_products_dataset |
| sellers | olist_sellers_dataset |
| customers | olist_customers_dataset（可选，用于区域分析） |

可选参数：`start_date`、`end_date`（默认最近 7 天）、`output_dir`（默认 `./reports/weekly_{date}/`）

表结构详见 [olist-data-reference/reference.md](../olist-data-reference/reference.md)。

## 工具

| 工具 | 用途 |
|------|------|
| 文件读取 | 加载 CSV/Excel |
| Python (pandas) | 清洗、Join、聚合、派生字段 |
| matplotlib / seaborn | 趋势图、对比图、TOP N 条形图（**须先配置中文字体**，见下） |
| Write / 报告输出 | Markdown 周报；可选 python-pptx / python-docx |
| WebSearch | 仅当需解释巴西节假日等外部因素时 |

## 执行流程

### 0. 校验（必做）

```bash
python .cursor/skills/weekly-ops-report/scripts/validate_tables.py <data_dir>
```

失败则中止，列出缺失表或字段。

### 1. 加载与连接

1. 读取各表，统一 `order_purchase_timestamp` 等为 datetime
2. Join：`orders` ← `order_items` ← `products` / `sellers`；左连 `reviews`、`payments`
3. 记录连接丢失率（无明细的订单占比）；>5% 写入警告

### 2. 核心指标（本周期 vs 上周期）

- 订单量、GMV、平均客单价
- **延迟率**（delivered 且实际送达 > 预计送达）
- **差评率**（review_score ≤ 2 / 有评论订单）
- **取消率**（order_status = canceled）
- 卖家风险 TOP10（调用 seller-risk-scan 口径，见该 skill）

### 3. 子分析（可并行）

| 模块 | 对应 skill | 产出 |
|------|-----------|------|
| 履约延迟 | delay-diagnosis | 延迟趋势、卖家/品类/区域 TOP |
| 差评归因 | review-issue-locator | 物流/价格/运费/品类/卖家关联 |
| 卖家风险 | seller-risk-scan | 高风险卖家清单 |
| 品类体验 | category-experience-audit | 规模大但体验差类目 |

### 3.5 图表中文显示（必做，在 `plt.savefig` 之前）

`rcParams["font.sans-serif"]` 单独设置**不够**：`seaborn.set_theme()` 会把字体重置为 Arial，中文标题/轴标签会显示为方框。

**固定做法**：在脚本最前面、任何 `plt`/`sns` 作图之前执行：

```python
import sys
from pathlib import Path

_scripts = Path(__file__).resolve().parent / "scripts"
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))
from chart_zh_font import setup_chinese_chart

setup_chinese_chart()  # 绑定 C:\Windows\Fonts\msyh.ttc 等字体文件

from chart_zh_font import get_cjk_font_properties, apply_cjk_font
fp = get_cjk_font_properties()
ax.set_title("近8周延迟率趋势", fontproperties=fp)
ax.set_xticklabels(["准时/提前", "延迟>7天"], fontproperties=fp)  # 中文刻度必须显式传 fp
apply_cjk_font(ax, fig)  # 兜底：标题/轴/图例/色条
```

**禁止**仅依赖 `rcParams` 或 `sns.set_theme()` 后不再传 `fontproperties`；`bad_review_by_delay_bins` 等图的 **X 轴中文分箱标签** 必须用 `set_xticklabels(..., fontproperties=fp)`。

校验字体是否生效：

```bash
python .cursor/skills/weekly-ops-report/scripts/chart_zh_font.py
# 期望输出: OK: using font 'Microsoft YaHei'
```

若报「未找到可用的中文字体」：Windows 安装「微软雅黑」或 [Noto Sans CJK SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC)，然后重试。

子 skill 作图时同样必须先 `setup_chinese_chart()`，或复制 `scripts/chart_zh_font.py` 到分析脚本同目录。

### 4. 图表（至少 3 张 PNG，与数据同目录）

1. 近 N 周延迟率趋势（折线）
2. 延迟率 TOP10 卖家或品类（条形）
3. 差评率 vs 延迟天数散点或分箱对比

### 5. 明细表（至少 3 张，CSV 或 Markdown 表）

1. 风险卖家清单（seller_id, 订单量, 延迟率, 差评率, 风险分）
2. 问题品类清单（品类, 订单量, 差评率, 延迟率）
3. 本周异常订单样本（延迟>7天或差评且延迟）

### 6. 报告正文

使用以下模板写入 `report.md`：

```markdown
# 经营巡检周报 | {start_date} ~ {end_date}

## 一句话结论
{是否恶化、最主要风险、优先行动}

## 核心指标
| 指标 | 本周 | 上周 | 环比 |
|------|------|------|------|

## 履约与客户体验
{延迟、差评、取消要点，引用图表路径}

## 风险卖家 TOP5
{表格摘要}

## 问题品类 TOP5
{表格摘要}

## 行动建议
1. ...
2. ...

## 附录
- 图表：./charts/
- 明细：./tables/
```

每张图在正文中用相对路径嵌入：`![延迟趋势](./charts/delay_trend.png)`。

## 输出

- `report.md`（主交付）
- `charts/*.png`（≥3）
- `tables/*.csv` 或 Markdown 表（≥3）
- 可选：`report.pptx` / `report.docx`（推荐用 [report-assets-summary](../report-assets-summary/SKILL.md) 的 `export_report_docx.py` 从 charts+tables+summary 导出）

## 失败条件（中止）

- 关键表（orders, order_items, reviews）任一缺失
- `order_purchase_timestamp` 或送达时间字段无法解析
- 主表与明细表连接丢失率 > 20%
- 分析窗口内有效订单数 < 30（样本过小，结论不可靠）

## 人工接管点

- 涉及**卖家处罚、下架、赔偿**等建议时，仅输出「待人工确认」清单，不自动执行
- 环比异常波动 >50% 且无业务解释时，标注「需业务确认」
- 外部节假日/大促影响需 WebSearch 辅助解释时，由人确认是否采纳

## 关联 skill

- [report-assets-summary](../report-assets-summary/SKILL.md) — 基于本 skill 产出的 `charts/`、`tables/` 生成 `summary.md`
- [delay-diagnosis](../delay-diagnosis/SKILL.md)
- [review-issue-locator](../review-issue-locator/SKILL.md)
- [seller-risk-scan](../seller-risk-scan/SKILL.md)
- [category-experience-audit](../category-experience-audit/SKILL.md)
