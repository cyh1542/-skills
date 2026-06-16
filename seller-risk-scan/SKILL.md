---
name: seller-risk-scan
description: >-
  扫描 Olist 高风险卖家：销量高但延迟率高、差评多、取消率高，输出风险得分与清单。
  适用于平台风控、卖家治理、周报风险章节、卖家绩效考核。
---

# 卖家风险扫描 (seller_risk_scan)

## 适用场景

- 「哪些卖家在放大平台风险：销量高但延迟率高、评论差、取消率高？」
- 周报风险卖家模块、平台治理专项

## 输入

- `orders.csv`, `order_items.csv`, `reviews.csv`, `sellers.csv`
- 参数：`min_orders=50`（纳入排名的最低订单量）、`top_n=20`

## 工具

| 工具 | 用途 |
|------|------|
| pandas | 按 seller_id 聚合指标、计算风险分 |
| matplotlib | 风险散点图（销量 vs 延迟率，颜色=差评率） |

## 图表中文

作图前必须 `setup_chinese_chart()`，见 [chart_zh_font.py](../weekly-ops-report/scripts/chart_zh_font.py)。

## 执行流程

### 1. 卖家级聚合

按 `seller_id` 统计（分析窗口内）：

| 指标 | 计算 |
|------|------|
| order_count | 订单数 |
| gmv | sum(price) |
| late_rate | 延迟 delivered 订单 / delivered 总数 |
| bad_review_rate | 差评数 / 有评论订单数 |
| cancel_rate | canceled / 全部订单 |

### 2. 风险得分（0-100，越高越危险）

```python
# 归一化后加权，仅对 order_count >= min_orders 的卖家
risk_score = (
    0.35 * norm(late_rate)
    + 0.35 * norm(bad_review_rate)
    + 0.20 * norm(cancel_rate)
    + 0.10 * norm(order_count)  # 规模大放大风险
)
```

标注风险等级：≥70 高，40-69 中，<40 低。

### 3. 筛选「高风险且高销量」

默认：`order_count >= P75` 且 `risk_score >= 60`，或用户自定义阈值。

### 4. 图表

- 散点图：X=订单量，Y=延迟率，点大小=GMV，颜色=差评率，标注 TOP5 卖家 ID

### 5. 输出清单表

| seller_id | 订单量 | 延迟率 | 差评率 | 取消率 | 风险分 | 等级 |
|-----------|--------|--------|--------|--------|--------|------|

附一句话：`{N} 个卖家同时处于高销量与高风险区间，建议优先巡检。`

## 输出

- `seller_risk_list.csv`
- `seller_risk_summary.md`
- `charts/seller_risk_scatter.png`

## 失败条件

- 无 seller_id 可关联的 order_items
- 满足 min_orders 的卖家数 < 5

## 人工接管点

- **禁止**自动下架、罚款、封店；仅输出「建议重点关注」清单
- 风险分阈值调整需业务方确认
