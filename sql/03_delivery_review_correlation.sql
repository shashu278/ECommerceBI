SELECT
    WIDTH_BUCKET(EXTRACT(DAY FROM (order_delivered_customer_date - order_estimated_delivery_date)), -30, 30, 12) AS delay_bucket,
    ROUND(AVG(r.review_score), 2) AS avg_review_score,
    COUNT(*) AS n_orders
FROM orders o
JOIN order_reviews r ON o.order_id = r.order_id
WHERE o.order_delivered_customer_date IS NOT NULL
GROUP BY delay_bucket
ORDER BY delay_bucket;