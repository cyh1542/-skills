---
name: category-experience-audit
description: >-
  审计 Olist 品类体验：识别规模大但延迟高、差评多的「问题类目」。
  输出品类健康矩阵图与改进优先级。适用于品类运营、体验复盘、周报品类章节。
---

# 品类体验审计 (category_experience_audit)

## 适用场景

- 「哪些品类是规模大但体验差的问题类目？」
- 品类结构优化、体验与规模平衡分析

## 输入

- `orders.csv`, `order_items.csv`, `products.csv`, `reviews.csv`
- 参数：`min_category_orders=30`

## 工具

| 工具 | 用途 |
|------|------|
| pandas | 按 product_category_name 聚合 |
| matplotlib | 品类健康矩阵（规模 vs 体验） |

## 图表中文

作图前必须 `setup_chinese_chart()`，见 [chart_zh_font.py](../weekly-ops-report/scripts/chart_zh_font.py)。

## 执行流程

### 1. 品类指标

| 指标 | 说明 |
|------|------|
| order_count | 订单行数或订单数 |
| gmv_share | 占全平台 GMV 比例 |
| late_rate | 延迟率 |
| bad_review_rate | 差评率 |

### 2. 问题类目定义

同时满足：

- **规模大**：order_count ≥ P60 或 gmv_share ≥ 2%
- **体验差**：late_rate ≥ 全平台延迟率 + 5pp，或 bad_review_rate ≥ 全平台 + 5pp

### 3. 健康矩阵图

- X 轴：订单量（规模）
- Y 轴：体验分 = 100 - (late_rate×50 + bad_review_rate×50)（可调整）
- 四象限标注：明星 / 问题 / 长尾 / 潜力

### 4. 优先级排序

```text
priority = order_count * (late_rate + bad_review_rate)
```

输出 TOP10 问题类目及改进方向（物流、描述、品控等假设，标注「待验证」）。

## 输出

- `category_health.md`（结论 + 矩阵图）
- `tables/problem_categories.csv`
- `charts/category_health_matrix.png`

## 失败条件

- products 无法映射到 order_items 的比例 > 15%
- 有效品类数 < 5

## 人工接管点

- 品类下架/收缩建议需品类负责人确认
- 翻译类目名（product_category_name 为葡语）时可用映射表，不自动改商品结构
