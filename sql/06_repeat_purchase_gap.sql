WITH ordered AS (
    SELECT c.customer_unique_id, o.order_purchase_timestamp,
           ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp) AS rn
    FROM orders o JOIN customers c ON o.customer_id = c.customer_id
)
SELECT a.customer_unique_id,
       a.order_purchase_timestamp AS first_order,
       b.order_purchase_timestamp AS second_order,
       EXTRACT(DAY FROM (b.order_purchase_timestamp - a.order_purchase_timestamp)) AS gap_days
FROM ordered a
JOIN ordered b ON a.customer_unique_id = b.customer_unique_id AND b.rn = 2
WHERE a.rn = 1;