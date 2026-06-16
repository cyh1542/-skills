---
name: review-issue-locator
description: >-
  定位 Olist 差评根因：分析差评与物流时效、价格、运费、品类、卖家的关联。
  输出归因表、对比图与改进建议。适用于差评分析、客户体验、评论归因、体验优化。
---

# 差评归因定位 (review_issue_locator)

## 适用场景

- 「差评是否与物流时效、价格、运费、品类或卖家有关？」
- 体验复盘、客诉分析、周报客户体验章节

## 输入

- `orders.csv`, `order_items.csv`, `reviews.csv`（必选）
- `products.csv`, `payments.csv`（可选，用于品类与支付维度）

参数：`bad_review_threshold=2`（review_score ≤ 2 为差评）

## 工具

| 工具 | 用途 |
|------|------|
| pandas | 合并评论与订单、分箱、分组聚合 |
| matplotlib/seaborn | 差评率对比图、散点/箱线图 |
| scipy 或 pandas corr | 相关性（可选，样本足够时） |

## 图表中文

作图前必须 `setup_chinese_chart()`，见 [chart_zh_font.py](../weekly-ops-report/scripts/chart_zh_font.py) 与主 skill「3.5 图表中文显示」。

## 执行流程

### 1. 构建分析宽表

Join：`reviews` → `orders` → `order_items` → `products`。

派生字段：

| 字段 | 说明 |
|------|------|
| is_bad_review | review_score ≤ 2 |
| is_late | 实际送达 > 预计送达 |
| delay_days | 延迟天数 |
| order_amount | sum(price + freight_value) per order |
| freight_ratio | freight / order_amount |
| avg_item_price | mean(price) per order |

### 2. 单因素对比

对每个因素，比较**差评组 vs 非差评组**（或差评率 by 分箱）：

| 因素 | 方法 |
|------|------|
| 物流时效 | 延迟 vs 准时：差评率差值；delay_days 分箱（0,1-3,4-7,7+） |
| 价格 | 订单金额分位数（Q1-Q4）差评率 |
| 运费 | freight_ratio 分箱差评率 |
| 品类 | 各 product_category_name 差评率、订单量 |
| 卖家 | 各 seller_id 差评率（订单量≥20） |

### 3. 多因素摘要

输出「贡献度排序」：按差评率差值或 lift 排序 TOP 因素（不必训练复杂模型，优先可解释表格）。

```markdown
| 因素 | 差评率 | 整体差评率 | 差值(lift) |
|------|--------|------------|------------|
| 延迟>7天 | 28% | 8% | +20pp |
```

### 4. 图表（≥2 张 PNG）

1. **延迟天数分箱 vs 差评率**（柱状）
2. **TOP10 高差评品类或卖家**（条形，标注样本量）

可选：价格/运费分箱差评率对比图。

### 5. 结论与建议

```markdown
## 差评归因结论

**主要关联**：{如：延迟>3天差评率显著升高；高运费占比订单差评更集中}

**高差评品类**：...
**高差评卖家**：...

**改进建议**（不含处罚，仅运营）：
1. 优先优化 {品类/卖家} 的预计送达准确性
2. 对高运费订单设置预期管理
```

## 输出

- `review_attribution.md`
- `charts/bad_review_by_delay_bins.png`, `charts/bad_review_top_categories.png`
- `tables/review_by_factor.csv`

## 失败条件

- reviews 表缺失或 review_score 无法解析
- 有评论的订单 < 100
- 无法关联 orders 的比例 > 15%

## 人工接管点

- 不向客户自动发送道歉/补偿话术
- 涉及「卖家责任认定」用于处罚时，需人工复核样本订单
