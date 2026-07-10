import pandas as pd
import numpy as np
import os
import joblib
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score
from sklearn.impute import SimpleImputer

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

# Load data and EXCLUDE censored customers from training
df = pd.read_sql("SELECT * FROM model_features", engine)
trainable_df = df[df['is_censored'] == False].copy()
censored_df = df[df['is_censored'] == True].copy()

# Define features (X) and target (y)
X = trainable_df.drop(columns=['customer_unique_id', 'is_repeat_customer', 'is_censored'])
y = trainable_df['is_repeat_customer']

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Build Pipeline
pipe = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("smote", SMOTE(random_state=42)),
    ("model", XGBClassifier(eval_metric="logloss", random_state=42, use_label_encoder=False))
])

print("Running Cross-Validation...")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="roc_auc")
print(f"Mean CV ROC-AUC: {np.mean(scores):.3f}")

# Fit final model
pipe.fit(X_train, y_train)

# Calculate Baseline (Naive rule: assume high spenders are the only repeaters)
# Using strictly the first order's spend
baseline_preds = (X_test["first_order_total_spend"] > X_test["first_order_total_spend"].median()).astype(int)

# Bootstrap CI on AUC lift to prove your model beats a naive guess
diffs = []
print("Calculating Bootstrap Confidence Intervals...")
for _ in range(1000):
    idx = np.random.choice(len(y_test), len(y_test), replace=True)
    model_auc = roc_auc_score(y_test.iloc[idx], pipe.predict_proba(X_test.iloc[idx])[:,1])
    base_auc = roc_auc_score(y_test.iloc[idx], baseline_preds.iloc[idx])
    diffs.append(model_auc - base_auc)

print(f"AUC lift 95% CI: [{np.percentile(diffs, 2.5):.3f}, {np.percentile(diffs, 97.5):.3f}]")

# Save the model
joblib.dump(pipe, "src/model.pkl")
print("Model saved to src/model.pkl")

# Score EVERY customer
X_all = df.drop(columns=['customer_unique_id', 'is_repeat_customer', 'is_censored'])

# Predict probability of retention (Class 1), so Churn Risk is 1 - Retention Prob
df['retention_prob'] = pipe.predict_proba(X_all)[:, 1]
df['churn_risk_score'] = 1 - df['retention_prob']

# Assign Business Tiers
# Note: Lower bound shifted to -0.1 to safely catch absolute 0.0 scores
df['risk_tier'] = pd.cut(
    df['churn_risk_score'], 
    bins=[-0.1, 0.4, 0.7, 1.0], 
    labels=['Low Risk', 'Medium Risk', 'High Risk']
)

# Calculate Revenue at Risk (Assuming first order spend is a proxy for Predicted LTV here)
df['predicted_ltv'] = df['first_order_total_spend'] * 1.2  # Simple 20% margin assumption for LTV
df['revenue_at_risk'] = df['predicted_ltv'] * df['churn_risk_score']

# Isolate the final columns and push back to Supabase
final_predictions = df[['customer_unique_id', 'churn_risk_score', 'risk_tier', 'predicted_ltv', 'revenue_at_risk']]
final_predictions.to_sql("customer_predictions", engine, if_exists="replace", index=False)

print("Scoring complete. customer_predictions table is live in Supabase.")