"""Cancellation / no-show prediction: predicts the probability an appointment
will be cancelled or result in a no-show, using features known at scheduling
time. Baseline: logistic regression. Challenger: HistGradientBoostingClassifier.
Reports ROC-AUC, PR-AUC and a calibration-style bucket summary.
"""
from __future__ import annotations
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.preprocessing import OrdinalEncoder, StandardScaler

from ..utils.config import load_yaml
from ..utils.logging_config import get_logger
from ..utils.paths import DATA_PROCESSED
from . import model_registry

log = get_logger(__name__)

CATEGORICAL = ["location_id", "service_type_id", "urgency"]
NUMERIC = ["travel_minutes", "complexity_score", "day_of_week", "is_weekend", "month", "is_winter"]
TARGET = "cancelled_label"


def run() -> dict:
    df = pd.read_csv(DATA_PROCESSED / "cancellation_features.csv")
    enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X_cat = enc.fit_transform(df[CATEGORICAL].astype(str))
    X = pd.concat([pd.DataFrame(X_cat, columns=CATEGORICAL), df[NUMERIC].reset_index(drop=True)], axis=1)
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    baseline = LogisticRegression(max_iter=1000, class_weight="balanced")
    baseline.fit(X_train_s, y_train)
    base_proba = baseline.predict_proba(X_test_s)[:, 1]
    base_auc = roc_auc_score(y_test, base_proba)
    base_ap = average_precision_score(y_test, base_proba)

    model = HistGradientBoostingClassifier(max_depth=5, learning_rate=0.08, max_iter=300,
                                            random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    ap = average_precision_score(y_test, proba)

    metrics = {
        "baseline_logreg_roc_auc": round(float(base_auc), 4),
        "baseline_logreg_pr_auc": round(float(base_ap), 4),
        "challenger_hgb_roc_auc": round(float(auc), 4),
        "challenger_hgb_pr_auc": round(float(ap), 4),
        "positive_rate": round(float(y.mean()), 4),
        "n_train": int(len(X_train)), "n_test": int(len(X_test)),
    }
    thresholds = load_yaml("monitoring.yml")["model_thresholds"]["cancellation_prediction"]
    status = "breach" if auc < thresholds["breach_below"] else ("warning" if auc < thresholds["warn_below"] else "healthy")

    model_registry.register(
        name="cancellation_prediction", version="1.0.0", metrics=metrics, threshold_status=status,
        artifact_path="in-memory (retrained on each pipeline run)",
        notes="HistGradientBoostingClassifier challenger vs. class-weighted logistic-regression baseline.")

    log.info("Cancellation prediction metrics: auc=%.3f status=%s", auc, status)
    return {"metrics": metrics, "status": status}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
