"""Service-level (SLA) breach prediction: predicts, at request-intake time,
whether a request is at risk of breaching its response-time SLA target.
Baseline: logistic regression on urgency alone. Challenger: HistGradientBoostingClassifier
with the full feature set. Reports ROC-AUC and precision/recall at the
operating threshold used for the "at-risk" flag on the Service Backlog dashboard page.
"""
from __future__ import annotations
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, precision_score, recall_score
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

from ..utils.config import load_yaml
from ..utils.logging_config import get_logger
from ..utils.paths import DATA_PROCESSED
from . import model_registry

log = get_logger(__name__)

CATEGORICAL = ["location_id", "service_type_id", "urgency"]
NUMERIC = ["complexity_score", "day_of_week", "is_weekend", "month", "is_winter"]
TARGET = "breach_label"
OPERATING_THRESHOLD = 0.35  # flags a request as "at risk" above this predicted probability


def run() -> dict:
    df = pd.read_csv(DATA_PROCESSED / "sla_breach_features.csv")
    enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X_cat = enc.fit_transform(df[CATEGORICAL].astype(str))
    X = pd.concat([pd.DataFrame(X_cat, columns=CATEGORICAL), df[NUMERIC].reset_index(drop=True)], axis=1)
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    scaler = StandardScaler()
    baseline = LogisticRegression(max_iter=1000, class_weight="balanced")
    baseline.fit(scaler.fit_transform(X_train[["urgency"]]), y_train)
    base_proba = baseline.predict_proba(scaler.transform(X_test[["urgency"]]))[:, 1]
    base_auc = roc_auc_score(y_test, base_proba)

    model = HistGradientBoostingClassifier(max_depth=5, learning_rate=0.07, max_iter=300,
                                            random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    pred = (proba >= OPERATING_THRESHOLD).astype(int)
    precision = precision_score(y_test, pred, zero_division=0)
    recall = recall_score(y_test, pred, zero_division=0)

    metrics = {
        "baseline_urgency_only_roc_auc": round(float(base_auc), 4),
        "challenger_hgb_roc_auc": round(float(auc), 4),
        "operating_threshold": OPERATING_THRESHOLD,
        "precision_at_threshold": round(float(precision), 4),
        "recall_at_threshold": round(float(recall), 4),
        "breach_rate": round(float(y.mean()), 4),
        "n_train": int(len(X_train)), "n_test": int(len(X_test)),
    }
    thresholds = load_yaml("monitoring.yml")["model_thresholds"]["service_level_breach_prediction"]
    status = "breach" if auc < thresholds["breach_below"] else ("warning" if auc < thresholds["warn_below"] else "healthy")

    model_registry.register(
        name="service_level_breach_prediction", version="1.0.0", metrics=metrics, threshold_status=status,
        artifact_path="in-memory (retrained on each pipeline run)",
        notes="Flags requests likely to breach SLA at intake so coordinators can prioritise scheduling.")

    log.info("SLA breach prediction metrics: auc=%.3f status=%s", auc, status)
    return {"metrics": metrics, "status": status}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
