---
name: delay-diagnosis
description: >-
  诊断 Olist 订单履约延迟：近周期是否恶化、延迟集中在哪些卖家/品类/区域。
  输出趋势图、TOP 明细与归因结论。适用于延迟分析、履约巡检、卖家/区域履约排查。
---

# 延迟履约诊断 (delay_diagnosis)

## 适用场景

- 「近一周/月订单履约是否恶化？」
- 「延迟交付主要集中在哪些卖家、品类或区域？」
- 周报中的履约模块，或单独履约专项分析

## 输入

- `orders.csv`（必选）：order_id, order_status, order_purchase_timestamp, order_delivered_customer_date, order_estimated_delivery_date
- `order_items.csv`（必选）：order_id, seller_id, product_id
- `products.csv`（品类维度）
- `sellers.csv`、`customers.csv`（区域维度，可选）

参数：`window_days=7`，`compare_previous=true`（与上一等长窗口对比）

## 工具

| 工具 | 用途 |
|------|------|
| pandas | 过滤 delivered 订单、计算延迟天数与延迟率 |
| matplotlib/seaborn | 趋势图、TOP 条形图、区域热力（可选） |
| 文件写入 | 明细 CSV + 结论 Markdown |

## 图表中文

作图前必须调用 [weekly-ops-report/scripts/chart_zh_font.py](../weekly-ops-report/scripts/chart_zh_font.py) 中的 `setup_chinese_chart()`（`seaborn.set_theme()` 会覆盖字体导致中文方框）。详见主 skill「3.5 图表中文显示」。

## 执行流程

### 1. 数据准备

```python
# 仅分析已送达订单
delivered = orders[orders["order_status"] == "delivered"].copy()
delivered["is_late"] = (
    delivered["order_delivered_customer_date"]
    > delivered["order_estimated_delivery_date"]
)
delivered["delay_days"] = (
    delivered["order_delivered_customer_date"]
    - delivered["order_estimated_delivery_date"]
).dt.days
```

按 `order_purchase_timestamp` 过滤分析窗口。

### 2. 恶化判断

- 计算本窗口 vs 上窗口：**延迟率**、**平均延迟天数**、**P90 延迟天数**
- 恶化标准（满足任一）：延迟率环比上升 ≥2pp，或平均延迟天数上升 ≥1 天
- 输出：`{恶化/改善/持平} + 数值证据`

### 3. 维度下钻（各取 TOP10，样本量≥20）

| 维度 | 分组键 | 输出字段 |
|------|--------|----------|
| 卖家 | seller_id | 订单数, 延迟率, 平均延迟天数 |
| 品类 | product_category_name | 同上 |
| 区域 | customer_state 或 seller_state | 同上 |

Join：`orders` → `order_items` → `products` / `customers` / `sellers`。

### 4. 图表（≥2 张，保存 PNG）

1. **周/日延迟率趋势**（折线，含本周期与上周期对比虚线可选）
2. **延迟率 TOP10 卖家或品类**（横向条形，标注订单量）

### 5. 结论模板

```markdown
## 延迟诊断结论

**整体**：{恶化/改善/持平}。本周期延迟率 {x%}（上期 {y%}，环比 {z}pp）。

**集中卖家**：{seller_id 列表及延迟率}
**集中品类**：{品类列表}
**集中区域**：{州/市列表}

**建议**：{如：约谈 TOP3 卖家、检查某品类仓配、关注某州物流}
```

## 输出

- `delay_diagnosis.md`（结论 + 嵌入图表）
- `charts/delay_trend.png`, `charts/delay_top_sellers.png`
- `tables/delay_by_seller.csv`, `delay_by_category.csv`, `delay_by_region.csv`

## 失败条件

- orders 表缺少送达/预计送达时间字段
- 分析窗口内 delivered 订单 < 50
- order_items 无法匹配超过 20% 的 delivered 订单

## 人工接管点

- 建议「暂停合作/切换物流」前必须人工确认
- 单卖家订单量 <20 不纳入 TOP 排名，避免小样本误判
