import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# 1. Category translation
trans_df = pd.read_csv("data/product_category_name_translation.csv")

# Manually add the missing categories that cause the FK violation
missing_cats = pd.DataFrame({
    "product_category_name": ["pc_gamer", "portateis_cozinha_e_preparadores_de_alimentos"],
    "product_category_name_english": ["pc_gamer", "kitchen_and_food_preparators_portables"]
})
trans_df = pd.concat([trans_df, missing_cats], ignore_index=True)

trans_df.to_sql("category_translation", engine, if_exists="append", index=False)

# 2. Sellers, Products, Customers (no dependencies among these)
pd.read_csv("data/olist_sellers_dataset.csv").rename(columns=lambda c: c.replace("_dataset","")).to_sql(
    "sellers", engine, if_exists="append", index=False)

products = pd.read_csv("data/olist_products_dataset.csv")[
    ["product_id","product_category_name","product_weight_g",
     "product_length_cm","product_height_cm","product_width_cm"]]
products.to_sql("products", engine, if_exists="append", index=False)

pd.read_csv("data/olist_customers_dataset.csv").to_sql(
    "customers", engine, if_exists="append", index=False)

# 3. Geolocation — DEDUPLICATE before loading (raw file has ~1M rows; you need ~19-20k)
geo = pd.read_csv("data/olist_geolocation_dataset.csv")
geo_clean = geo.groupby("geolocation_zip_code_prefix").agg(
    lat=("geolocation_lat","mean"),
    lng=("geolocation_lng","mean"),
    city=("geolocation_city","first"),
    state=("geolocation_state","first")
).reset_index().rename(columns={"geolocation_zip_code_prefix":"zip_code_prefix"})
geo_clean.to_sql("geolocation", engine, if_exists="append", index=False)

# 4. Orders (parses dates!)
orders = pd.read_csv("data/olist_orders_dataset.csv", parse_dates=[
    "order_purchase_timestamp","order_delivered_customer_date","order_estimated_delivery_date"])
orders[["order_id","customer_id","order_status","order_purchase_timestamp",
        "order_delivered_customer_date","order_estimated_delivery_date"]].to_sql(
    "orders", engine, if_exists="append", index=False)

# 5. Order items, payments, reviews
order_items_df = pd.read_csv("data/olist_order_items_dataset.csv")[
    ["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"]
]
order_items_df.to_sql("order_items", engine, if_exists="append", index=False)
pd.read_csv("data/olist_order_payments_dataset.csv").to_sql(
    "order_payments", engine, if_exists="append", index=False)
pd.read_csv("data/olist_order_reviews_dataset.csv")[
    ["review_id","order_id","review_score","review_comment_message","review_creation_date"]
].to_sql("order_reviews", engine, if_exists="append", index=False)

print("Load complete.")