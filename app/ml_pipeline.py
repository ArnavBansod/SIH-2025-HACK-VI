"""
Simple ML pipeline:
- Accept merged DataFrame with expected columns (student_id, attendance, test_score, fee_paid, attempts, date)
- Engineer a few features (attendance, recent score trend, attempts, fee_delayed)
- Train a lightweight classifier/regressor (RandomForest) if labeled data provided, otherwise use rule-based scoring
- Save/load model to disk (joblib)
"""

from typing import Tuple, Dict, Any
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib
import os
from config import settings

MODEL_PATH = settings.MODEL_PATH

def feature_engineer(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    # Ensure expected columns
    # fill missing numeric with reasonable defaults
    df2["attendance"] = pd.to_numeric(df2.get("attendance", np.nan), errors="coerce").fillna(0)
    df2["test_score"] = pd.to_numeric(df2.get("test_score", np.nan), errors="coerce").fillna(0)
    df2["attempts"] = pd.to_numeric(df2.get("attempts", 0), errors="coerce").fillna(0)
    df2["fee_paid"] = df2.get("fee_paid", True).astype(bool)
    # Score trend: if previous_score exists, compute drop
    if "prev_test_score" in df2.columns:
        df2["score_drop"] = df2["prev_test_score"] - df2["test_score"]
    else:
        df2["score_drop"] = 0.0
    # Fee delinquent numeric
    if "days_past_due" in df2.columns:
        df2["days_past_due"] = pd.to_numeric(df2["days_past_due"], errors="coerce").fillna(0)
    else:
        df2["days_past_due"] = 0
    # Build final features
    features = df2[["attendance", "test_score", "score_drop", "attempts", "days_past_due"]].copy()
    # Clip scales
    features["attendance"] = features["attendance"].clip(0,100)
    features["test_score"] = features["test_score"].clip(0,100)
    return features

def rule_based_score(row: pd.Series) -> Tuple[float, str, Dict[str, Any]]:
    """
    Combine rule-based heuristics into a risk score (0-1).
    Higher score indicates higher risk.
    Return (risk_score, risk_label, details).
    """
    score = 0.0
    details = {}
    # Attendance: below threshold increases risk
    if row["attendance"] < settings.ATTENDANCE_THRESHOLD:
        # linear mapping: 0% -> +0.6, threshold-> +0.0
        att_risk = max(0.0, (settings.ATTENDANCE_THRESHOLD - row["attendance"]) / settings.ATTENDANCE_THRESHOLD) * 0.6
    else:
        att_risk = 0.0
    # Test score drop
    if row["score_drop"] > settings.TEST_DROP_THRESHOLD:
        drop_risk = min(0.3, (row["score_drop"] / 100.0) * 0.3 * 10)  # scaled
    else:
        drop_risk = 0.0
    # Attempts high
    attempts_risk = min(0.2, (row["attempts"] / 5.0) * 0.2)
    # Fee overdue
    fee_risk = 0.0
    if row["days_past_due"] > settings.FEE_DELINQUENT_DAYS:
        fee_risk = 0.2
    score = max(0.0, min(1.0, att_risk + drop_risk + attempts_risk + fee_risk))
    # label mapping
    if score >= 0.7:
        label = "high"
    elif score >= 0.35:
        label = "medium"
    else:
        label = "low"
    details.update({"attendance_component": att_risk, "drop_component": drop_risk, "attempts_component": attempts_risk, "fee_component": fee_risk})
    return float(score), label, details

def train_model(X: pd.DataFrame, y: pd.Series) -> Pipeline:
    """
    Train a RandomForest classifier.
    y should be labels: 0 (low), 1 (medium), 2 (high)
    """
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    pipe = Pipeline([("scaler", StandardScaler()), ("rf", clf)])
    pipe.fit(X, y)
    # persist
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    return pipe

def load_model() -> Pipeline | None:
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None

def predict_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Accept merged df, run engineering, then predict:
    - If model exists, use model to get label probabilities and map to risk score
    - Otherwise fallback to rule-based scoring
    Return a DataFrame with student_id, risk_score, risk_label, details
    """
    features = feature_engineer(df)
    model = load_model()
    results = []
    for idx, row in features.iterrows():
        if model:
            # model predicts classes 0,1,2
            prob = model.predict_proba([row.values])[0]
            # map to score: weighted by probabilities (0->low, 2->high)
            risk_score = float((prob[1] * 0.5) + (prob[2] * 1.0))  # simple mapping
            label_idx = int(np.argmax(prob))
            label = {0: "low", 1: "medium", 2: "high"}.get(label_idx, "low")
            details = {"proba": prob.tolist()}
        else:
            risk_score, label, details = rule_based_score(row)
        results.append({
            "student_id": df.iloc[idx].get("student_id"),
            "risk_score": risk_score,
            "risk_label": label,
            "details": details
        })
    return pd.DataFrame(results)
