# Brazilian E-Commerce Delivery Experience Analytics

**E-commerce Analytics | SQL Data Modeling | Customer Experience | Logistics Performance | Machine Learning | Storytelling Dashboard**

This project analyzes the Brazilian Olist public e-commerce dataset to understand how logistics, payments, product categories and delivery performance affect customer satisfaction.

The central story is simple: **in marketplace operations, delivery experience often becomes the review**. Customer dissatisfaction is not only a product issue; it is shaped by the full post-purchase chain: promise, distance, freight, seller structure, delivery time and communication.

## Interactive storytelling dashboard

**[Open the dashboard →](https://luandarodrigues.github.io/olist-delivery-experience-analytics/)**

The dashboard is built as a Power BI-style storytelling panel using the raw CSV files from the repository. It calculates business insights directly from the data and is organized as an analytical narrative:

1. Executive story
2. Raw → clean mart
3. Delay hurts reviews
4. Geography changes cost
5. Category exposure
6. Payments and value
7. Predictive dissatisfaction layer
8. Business scenarios
9. Final storyline

## Business question

How can an e-commerce marketplace identify operational factors that drive poor customer reviews and use them to improve logistics, seller performance and customer experience?

## Dataset

The Olist dataset contains anonymized commercial data from Brazilian marketplace orders between 2016 and 2018.

Main raw entities used:

- Orders
- Order items
- Payments
- Reviews
- Products
- Sellers
- Customers
- Product category translation
- Geolocation reference, when available

## Raw to clean analytical mart

The project uses SQL-style modeling to transform relational raw tables into an order-level analytical mart.

```sql
WITH item_agg AS (...),
     payment_agg AS (...),
     review_agg AS (...)
SELECT
  orders.order_id,
  customer_state,
  delivery_days,
  delay_days,
  delayed_flag,
  items_count,
  sellers_count,
  freight_value,
  payment_value,
  review_score,
  CASE WHEN review_score <= 2 THEN 1 ELSE 0 END AS low_review_flag
FROM orders
LEFT JOIN customers
LEFT JOIN item_agg
LEFT JOIN payment_agg
LEFT JOIN review_agg;
```

This mart allows the analysis to connect operational facts with review outcomes at order level.

## Executive metrics

| Metric | Value |
|---|---:|
| Orders | 99,441 |
| Delivered orders | 96,478 |
| Items | 112,650 |
| Unique customers | 96,096 |
| Sellers | 3,095 |
| Products | 32,951 |
| Total GMV including freight | R$ 15,843,553.24 |
| Average order value | R$ 160.99 |
| Average review score | 4.09 |
| Low review rate, score <= 2 | 14.53% |
| Delivery delay rate | 8.11% |
| Average delivery time | 12.56 days |

## Hypotheses tested

| Hypothesis | Test | Business interpretation |
|---|---|---|
| Late deliveries have higher low-review risk | Compare low-review rate for delayed vs on-time/early orders | Delay is a customer experience risk driver |
| Cross-state delivery changes cost and time | Compare same-state vs cross-state delivery days and freight | Geography should be treated as an operating model, not just a location field |
| Some categories combine scale and dissatisfaction exposure | Rank categories by volume × low-review rate | Category prioritization should consider operational friction, not only sales volume |

## Main findings

- Delivery delay is the strongest signal associated with poor reviews.
- Cross-state deliveries are slower and more expensive than same-state deliveries.
- Same-state deliveries averaged around **7.9 days**, while cross-state deliveries averaged around **15.0 days**.
- Cross-state freight was also higher, with average freight of about **R$ 23.69** versus **R$ 13.46** for same-state deliveries.
- Product categories such as bed bath table, furniture decor and computers accessories combine high sales volume with relatively high low-review rates.
- Credit card is the dominant payment method by transaction volume and payment value.

## Machine learning task

A classification model was built to predict whether an order would receive a low review score, defined as review score <= 2.

| Model | Accuracy | ROC-AUC | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.768 | 0.752 | 0.296 | 0.597 | 0.396 |
| Random Forest | 0.839 | 0.759 | 0.397 | 0.519 | 0.450 |

The target is imbalanced, so recall and precision are more useful than accuracy alone. The model is not intended as a final production model, but as an analytical layer to identify dissatisfaction risk drivers.

## Most relevant features

| Feature | Business interpretation |
|---|---|
| delay_days | How late the order was compared with the estimated delivery date |
| delivery_days | Total time between purchase and delivery |
| items_count | Number of items in the order; proxy for complexity |
| freight | Logistics cost proxy |
| product_category_name_english | Product/category experience pattern |
| customer_state | Geographic demand and delivery pattern |
| sellers_count | Complexity of multi-seller orders |

## Business scenarios

The dashboard includes scenario logic to move from descriptive analytics to decision support:

| Scenario | Assumption | Use |
|---|---|---|
| Delay rescue | Reduce low-review exposure among late orders | Prioritize customer communication and exception handling |
| Category focus | Act on categories combining high scale and high dissatisfaction | Target seller/category operational improvements |
| Cross-state control | Treat long-distance delivery as a distinct SLA group | Improve delivery promise accuracy and freight monitoring |

## Tools and methods

- Python
- Pandas
- SQL / SQLite-ready analytical modeling
- Client-side JavaScript analytics
- Feature engineering
- Classification modeling
- Customer experience analytics
- Logistics performance analysis
- Business storytelling dashboard

## Files

```text
olist-delivery-experience-analytics/
├── README.md
├── data/
│   ├── raw Olist CSV files
│   └── derived analytical CSV files, when available
├── docs/
│   └── index.html
└── sql/
    └── 01_build_order_experience_mart.sql
```

## Why this project matters

This project shows how marketplace data can be turned into an operational intelligence layer. It connects commercial performance, logistics, seller structure and customer reviews into one analytical view.

The main analytical value is the storytelling: it reframes customer reviews as a late indicator of operational quality and shows how a business can move from reactive review monitoring to proactive dissatisfaction risk management.
