# Olist 数据表参考

Kaggle: Brazilian E-Commerce Public Dataset by Olist

## 表与关键字段

| 表名 | 常用文件名 | 关键字段 |
|------|-----------|----------|
| olist_orders_dataset | orders.csv | order_id, order_status, order_purchase_timestamp, order_delivered_customer_date, order_estimated_delivery_date |
| olist_order_items_dataset | order_items.csv | order_id, order_item_id, product_id, seller_id, price, freight_value |
| olist_order_payments_dataset | payments.csv | order_id, payment_sequential, payment_type, payment_installments, payment_value |
| olist_order_reviews_dataset | reviews.csv | review_id, order_id, review_score, review_creation_date, review_answer_timestamp |
| olist_products_dataset | products.csv | product_id, product_category_name, product_name_lenght, product_description_lenght, product_photos_qty |
| olist_customers_dataset | customers.csv | customer_id, customer_unique_id, customer_state, customer_city |
| olist_sellers_dataset | sellers.csv | seller_id, seller_state, seller_city |

## 标准 Join 路径

```
orders (order_id)
  ├── order_items (order_id) → products (product_id), sellers (seller_id)
  ├── payments (order_id)
  ├── reviews (order_id)
  └── customers (customer_id)
```

## 派生指标（统一口径）

| 指标 | 计算 |
|------|------|
| 是否延迟 | `order_delivered_customer_date > order_estimated_delivery_date`（仅 delivered 订单） |
| 延迟天数 | 实际送达 − 预计送达（天） |
| 差评 | `review_score <= 2` |
| 取消 | `order_status == 'canceled'` |
| 卖家风险得分 | 见 seller-risk-scan skill |

## 时间过滤

默认分析窗口：最近 7 天（周报）或用户指定 `start_date` / `end_date`。以 `order_purchase_timestamp` 为订单归属时间。
