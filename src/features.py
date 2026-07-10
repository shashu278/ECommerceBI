import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("Extracting enriched, time-bound features from database...")

# 1. Base aggregations + Context (Strictly isolated to FIRST order)
query_features = """
WITH first_orders AS (
    SELECT customer_id, order_id, order_purchase_timestamp, order_estimated_delivery_date, order_delivered_customer_date
    FROM (
        SELECT o.customer_id, o.order_id, o.order_purchase_timestamp, o.order_estimated_delivery_date, o.order_delivered_customer_date,
               ROW_NUMBER() OVER(PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp) as rn
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered'
    ) sub
    WHERE rn = 1
)
SELECT 
    c.customer_unique_id,
    AVG(oi.price) as first_order_avg_item_price,
    SUM(oi.price) as first_order_total_spend,
    AVG(oi.freight_value / NULLIF(oi.price, 0)) as first_order_freight_ratio,
    MAX(op.payment_installments) as max_installments,
    MAX(op.payment_type) as primary_payment_type,
    MAX(t.product_category_name_english) as primary_category,
    MAX(c.customer_state) as customer_state,
    EXTRACT(DAY FROM MAX(fo.order_delivered_customer_date - fo.order_estimated_delivery_date)) as delivery_delay_days
FROM customers c
JOIN first_orders fo ON c.customer_id = fo.customer_id
JOIN order_items oi ON fo.order_id = oi.order_id
LEFT JOIN order_payments op ON fo.order_id = op.order_id
LEFT JOIN products p ON oi.product_id = p.product_id
LEFT JOIN category_translation t ON p.product_category_name = t.product_category_name
GROUP BY c.customer_unique_id
"""
df_features = pd.read_sql(query_features, engine)

# 2. Convert categorical text columns to numeric using One-Hot Encoding
print("One-hot encoding categorical variables...")
df_features = pd.get_dummies(
    df_features, 
    columns=['primary_payment_type', 'primary_category', 'customer_state'], 
    dummy_na=True, 
    drop_first=True
)

# 3. Add Phase 3 Labels directly
df_labels = pd.read_sql("SELECT customer_unique_id, is_repeat_customer, is_censored FROM customer_labels", engine)
df_master = df_features.merge(df_labels, on="customer_unique_id", how="inner")

# Push to DB
df_master.to_sql("model_features", engine, if_exists="replace", index=False)
print(f"Feature engineering complete. Master table shape: {df_master.shape}")