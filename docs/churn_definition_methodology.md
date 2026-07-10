Methodology:
The churn intervention threshold is established at 123 days post-initial purchase.

Why 123 days?
I didn't want to pick a number out of thin air. By analyzing the repeat-purchase gap, I identified that 75% of organic reorders happen before 123 days. Why the 75th percentile and not the 90th (which was 247 days)? Because waiting 8 months for the 90th percentile means waiting too long. By day 123, the organic momentum of the first purchase has completely faded. This threshold isn't just a label; it defines the exact window where our retention team gets the highest ROI on intervention before the customer forgets about the brand.

Handling Censored Data:
A predictive model is only as good as its ground truth. Customers acquired within the final 123 days of our historical data haven't finished their lifecycle journey. Including them as "churned" would penalize our recent acquisition cohorts. I quarantined these users through a censoring flag, ensuring our machine learning model only learns from fully matured customer lifecycles.