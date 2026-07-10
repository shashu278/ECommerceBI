WITH first_orders AS (
    SELECT c.customer_unique_id,
           DATE_TRUNC('month', MIN(o.order_purchase_timestamp)) AS cohort_month
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_unique_id) AS initial_customers
    FROM first_orders
    GROUP BY cohort_month
),
activity AS (
    SELECT f.cohort_month,
           EXTRACT(year FROM AGE(DATE_TRUNC('month', o.order_purchase_timestamp), f.cohort_month)) * 12 +
           EXTRACT(month FROM AGE(DATE_TRUNC('month', o.order_purchase_timestamp), f.cohort_month)) AS month_number,
           COUNT(DISTINCT f.customer_unique_id) AS active_customers
    FROM first_orders f
    JOIN customers c ON f.customer_unique_id = c.customer_unique_id
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY f.cohort_month, month_number
)
SELECT a.cohort_month, cs.initial_customers, a.month_number, a.active_customers,
       ROUND(a.active_customers::numeric / cs.initial_customers, 4) AS retention_rate
FROM activity a
JOIN cohort_sizes cs ON a.cohort_month = cs.cohort_month
ORDER BY a.cohort_month, a.month_number;