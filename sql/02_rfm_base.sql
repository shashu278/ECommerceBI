CREATE OR REPLACE VIEW rfm_base AS
WITH customer_orders AS (
    SELECT c.customer_unique_id, o.order_id, o.order_purchase_timestamp,
           SUM(oi.price) AS order_value
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id, o.order_id, o.order_purchase_timestamp
)
SELECT customer_unique_id,
       EXTRACT(DAY FROM ((SELECT MAX(order_purchase_timestamp) FROM orders) - MAX(order_purchase_timestamp))) AS recency,
       COUNT(DISTINCT order_id) AS frequency,
       SUM(order_value) AS monetary
FROM customer_orders
GROUP BY customer_unique_id;