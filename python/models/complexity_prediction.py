"""Case-complexity prediction: predicts a service request's complexity tier
(Low / Medium / High / Critical) at intake using only request-level and
calendar features -- no protected attributes are used, consistent with
governance/model_card.md.

Baseline: majority-class + simple rule-of-thumb on urgency. Challenger:
HistGradientBoostingClassifier. Reports accuracy, macro F1 and a confusion
matrix summary.
"""
from __future__ import annotations
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import OrdinalEncoder

from ..utils.config import load_yaml
from ..utils.logging_config import get_logger
from ..utils.paths import DATA_PROCESSED
from . import model_registry

log = get_logger(__name__)

CATEGORICAL = ["location_id", "service_type_id", "urgency", "requested_by", "requested_channel"]
NUMERIC = ["day_of_week", "is_weekend", "month", "is_winter", "week_of_year"]
TARGET = "complexity_tier"


def run() -> dict:
    df = pd.read_csv(DATA_PROCESSED / "complexity_features.csv")
    df = df.dropna(subset=[TARGET]).reset_index(drop=True)

    enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X_cat = enc.fit_transform(df[CATEGORICAL].astype(str))
    X = pd.concat([pd.DataFrame(X_cat, columns=CATEGORICAL), df[NUMERIC].reset_index(drop=True)], axis=1)
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

    baseline = DummyClassifier(strategy="most_frequent", random_state=42)
    baseline.fit(X_train, y_train)
    base_pred = baseline.predict(X_test)
    base_acc = accuracy_score(y_test, base_pred)
    base_f1 = f1_score(y_test, base_pred, average="macro", zero_division=0)

    model = HistGradientBoostingClassifier(max_depth=6, learning_rate=0.08, max_iter=300, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    macro_f1 = f1_score(y_test, pred, average="macro", zero_division=0)
    labels = sorted(y.unique())
    cm = confusion_matrix(y_test, pred, labels=labels).tolist()

    metrics = {
        "baseline_majority_class_accuracy": round(float(base_acc), 4),
        "baseline_majority_class_macro_f1": round(float(base_f1), 4),
        "challenger_accuracy": round(float(acc), 4),
        "challenger_macro_f1": round(float(macro_f1), 4),
        "labels": labels,
        "confusion_matrix": cm,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }
    thresholds = load_yaml("monitoring.yml")["model_thresholds"]["complexity_prediction"]
    status = "breach" if macro_f1 < thresholds["breach_below"] else ("warning" if macro_f1 < thresholds["warn_below"] else "healthy")

    importances = getattr(model, "feature_importances_", None)
    top_features = None
    if importances is not None:
        top_features = sorted(zip(X.columns, importances), key=lambda t: -t[1])[:5]
        top_features = [(f, round(float(v), 4)) for f, v in top_features]

    model_registry.register(
        name="complexity_prediction", version="1.0.0", metrics=metrics, threshold_status=status,
        artifact_path="in-memory (retrained on each pipeline run)",
        notes=f"Top drivers (permutation-free HGB importance): {top_features}")

    log.info("Complexity prediction metrics: acc=%.3f macro_f1=%.3f status=%s", acc, macro_f1, status)
    return {"metrics": metrics, "status": status, "top_features": top_features}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
