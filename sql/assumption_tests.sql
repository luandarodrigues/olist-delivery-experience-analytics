-- Olist Delivery Experience Analytics
-- SQL assumption tests over the order-level analytical mart.
-- The table expected by these queries is outputs/order_level_mart.csv loaded as order_mart.

-- 1. Does delivery delay increase low-review risk?
SELECT
    CASE WHEN late = 1 THEN 'late_delivery' ELSE 'on_time_or_early' END AS segment,
    COUNT(*) AS orders,
    AVG(CASE WHEN low_review = 1 THEN 1.0 ELSE 0.0 END) AS low_review_rate,
    AVG(review_score) AS avg_review_score,
    AVG(delivery_days) AS avg_delivery_days
FROM order_mart
WHERE delivered = 1
  AND review_score IS NOT NULL
GROUP BY segment
ORDER BY low_review_rate DESC;

-- 2. Are cross-state routes operationally harder?
SELECT
    CASE WHEN cross_state = 1 THEN 'cross_state' ELSE 'same_state' END AS route_type,
    COUNT(*) AS orders,
    AVG(delivery_days) AS avg_delivery_days,
    AVG(freight) AS avg_freight,
    AVG(CASE WHEN late = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
    AVG(CASE WHEN low_review = 1 THEN 1.0 ELSE 0.0 END) AS low_review_rate
FROM order_mart
WHERE delivered = 1
  AND review_score IS NOT NULL
GROUP BY route_type;

-- 3. Which categories combine volume and customer pain?
SELECT
    primary_category,
    COUNT(*) AS orders,
    AVG(CASE WHEN low_review = 1 THEN 1.0 ELSE 0.0 END) AS low_review_rate,
    AVG(CASE WHEN late = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
    AVG(freight) AS avg_freight,
    AVG(delivery_days) AS avg_delivery_days
FROM order_mart
WHERE delivered = 1
  AND review_score IS NOT NULL
GROUP BY primary_category
HAVING COUNT(*) >= 100
ORDER BY (low_review_rate * COUNT(*)) DESC
LIMIT 20;

-- 4. Does seller complexity add friction?
SELECT
    CASE WHEN sellers_count > 1 THEN 'multi_seller' ELSE 'single_seller' END AS seller_complexity,
    COUNT(*) AS orders,
    AVG(CASE WHEN low_review = 1 THEN 1.0 ELSE 0.0 END) AS low_review_rate,
    AVG(CASE WHEN late = 1 THEN 1.0 ELSE 0.0 END) AS delay_rate,
    AVG(delivery_days) AS avg_delivery_days
FROM order_mart
WHERE delivered = 1
  AND review_score IS NOT NULL
GROUP BY seller_complexity;
