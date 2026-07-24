# KPI & evaluation methodology (portfolio standard)

The one place that defines *how* every number across this portfolio is computed
and *why* that metric was chosen over the obvious-but-worse alternative. If a repo
reports a KPI, it computes it the way described here. The theme throughout: pick the
metric that survives the thing that breaks the naive one — imbalance, short series,
zeros, scale, and miscalibration.

## Part A — business KPIs

| KPI | Definition | Where it's used | Note |
|---|---|---|---|
| Revenue | Σ(units × price) over the period | sales-kpi, revops, platform | trailing 24 months unless stated |
| Gross margin / GM% | (revenue − COGS) / revenue | sales-kpi, revops, platform | margin €, and % of revenue |
| GMROI | gross margin € / average inventory cost | revops assortment | the ratio a range review leans on |
| YoY growth | (period − same period last year) / last year | sales-kpi, platform | seasonality-safe vs MoM |
| OTIF (service) | orders on-time **and** in-full / orders | platform | modelled; labelled as such |
| Fill rate | used volume / container volume | logistics-digital-twin | packing efficiency |
| Pick travel | Σ(SKU velocity × distance to slot) | logistics-digital-twin | the slotting objective |
| Discount leakage | margin recoverable by tightening off-invoice discount | sales-kpi | a €-quantified lever |
| Expected uplift | Σ prescribed levers vs current, on the seed | revops, platform | every € labelled measured/estimated |

**Rule:** a business KPI is only reported next to the assumption that produced it.
Estimates (e.g. €/km, contamination rate) are labelled "estimate" with the value
stated so a reader can change it.

## Part B — model evaluation metrics (and why not the naive one)

**Forecasting — MASE & RMSSE, under rolling-origin CV.**
MAPE explodes on the near-zero demand that intermittent SKUs are full of, and it
rewards under-forecasting. MASE scales error by the in-sample seasonal-naive error,
so 1.0 = "no better than naive" and it's comparable across series. RMSSE is the
squared-error sibling (the M5 metric). We validate with **rolling-origin
cross-validation** (expanding window, forecast the next block, roll forward) rather
than a single hold-out, because one split of a short series is luck, not evidence.
*Used in:* sales-kpi-analytics, revops-optimizer, distributor-intelligence-platform
(MASE 0.38), demand-forecast-net.

**Imbalanced classification — PR-AUC first, not accuracy or ROC-AUC.**
At 15% churn or 3% fraud, a "predict the majority" model scores 85–97% accuracy and
is useless. ROC-AUC is better but optimistic under heavy imbalance because the huge
true-negative pool inflates it. **PR-AUC** (precision vs recall) focuses on the rare
positive class that actually matters. *Used in:* churn-rfm-predictor, order-anomaly-ae,
revops decline model.

**Calibration — Brier, ECE, reliability curves.**
A probability is only decision-useful if "0.8" means it happens ~80% of the time.
We report the **Brier score** and **Expected Calibration Error**, show a reliability
curve, and apply **Platt/temperature calibration** on held-out logits *after* any
class weighting (weighting distorts probabilities; calibrating first would undo it).
*Used in:* churn-rfm-predictor.

**Multi-class text — macro-F1, not accuracy.**
Accuracy is dominated by big categories; **macro-F1** averages per-class F1 so a rare
category that the model ignores actually costs score. Reported with a confusion
matrix. *Used in:* sku-text-classifier.

**Regression that drives a decision — add regret, not just R².**
For pricing, a low RMSE model can still price badly. We also report **simulated
profit uplift / regret** vs the analytic optimum on held-out data, because accuracy
≠ good pricing. And we demonstrate the **endogeneity caveat** explicitly (a
confounder biases naive OLS; adding controls recovers the true elasticity). *Used in:*
price-elasticity-regressor, revops pricing.

**Optimization — always vs a named, fair baseline.**
An optimizer's result is meaningless without the baseline a practitioner would
actually use. We report the gap vs that baseline and don't hide it when it's small:
routing 4.6% below Clarke-Wright (a strong 1964 heuristic) and 31% below naive;
assortment MILP vs greedy GMROI with the honest note that the gap is small until a
second constraint binds. *Used in:* route-optimizer, revops assortment, logistics.

## Part C — reproducibility rules
- Fixed seeds; same seed → identical KPIs (enforced by tests).
- Synthetic data is labelled synthetic, every time.
- No metric is reported without the split/CV scheme that produced it.
- "As-measured": if a lever only wins under a condition, the condition is stated,
  not buried.

*Author: Dimitres Kisimov. Metric choices grounded in the standard literature
(M4/M5 for MASE/RMSSE; Saito & Rehmsmeier 2015 for PR-AUC under imbalance; Guo et al.
ICML 2017 for calibration/ECE).*
