-- Olist Delivery Experience Analytics
-- 01_build_order_experience_mart.sql
-- Purpose: transform raw marketplace tables into one analytical order-level mart.

DROP VIEW IF EXISTS order_experience_mart;

CREATE VIEW order_experience_mart AS
WITH item_agg AS (
    SELECT
        order_id,
        COUNT(*) AS items_count,
        COUNT(DISTINCT product_id) AS products_count,
        COUNT(DISTINCT seller_id) AS sellers_count,
        SUM(price) AS product_value,
        SUM(freight_value) AS freight_value
    FROM olist_order_items_dataset
    GROUP BY order_id
),
payment_agg AS (
    SELECT
        order_id,
        COUNT(*) AS payment_installments_count,
        SUM(payment_value) AS payment_value,
        MAX(payment_installments) AS max_installments,
        GROUP_CONCAT(DISTINCT payment_type) AS payment_types
    FROM olist_order_payments_dataset
    GROUP BY order_id
),
review_agg AS (
    SELECT
        order_id,
        AVG(review_score) AS review_score,
        CASE WHEN AVG(review_score) <= 2 THEN 1 ELSE 0 END AS low_review_flag
    FROM olist_order_reviews_dataset
    GROUP BY order_id
),
order_dates AS (
    SELECT
        o.order_id,
        o.customer_id,
        o.order_status,
        DATE(o.order_purchase_timestamp) AS purchase_date,
        DATE(o.order_delivered_customer_date) AS delivered_date,
        DATE(o.order_estimated_delivery_date) AS estimated_delivery_date,
        JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp) AS delivery_days,
        JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_estimated_delivery_date) AS delay_days,
        CASE
            WHEN o.order_delivered_customer_date IS NULL THEN NULL
            WHEN JULIANDAY(o.order_delivered_customer_date) > JULIANDAY(o.order_estimated_delivery_date) THEN 1
            ELSE 0
        END AS delayed_flag
    FROM olist_orders_dataset o
)
SELECT
    od.order_id,
    od.customer_id,
    c.customer_state,
    c.customer_city,
    od.order_status,
    od.purchase_date,
    od.delivered_date,
    od.estimated_delivery_date,
    od.delivery_days,
    od.delay_days,
    od.delayed_flag,
    ia.items_count,
    ia.products_count,
    ia.sellers_count,
    ia.product_value,
    ia.freight_value,
    pa.payment_value,
    pa.payment_installments_count,
    pa.max_installments,
    pa.payment_types,
    ra.review_score,
    ra.low_review_flag,
    CASE
        WHEN od.delay_days > 0 THEN 'late'
        WHEN od.delivery_days > 15 THEN 'slow_on_time'
        ELSE 'fast_or_expected'
    END AS delivery_experience_segment
FROM order_dates od
LEFT JOIN olist_customers_dataset c ON od.customer_id = c.customer_id
LEFT JOIN item_agg ia ON od.order_id = ia.order_id
LEFT JOIN payment_agg pa ON od.order_id = pa.order_id
LEFT JOIN review_agg ra ON od.order_id = ra.order_id;
