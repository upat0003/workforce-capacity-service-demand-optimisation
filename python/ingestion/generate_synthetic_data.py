"""Synthetic source-system data generator.

Produces bronze-layer raw extracts for a multi-region field and community
services organisation: rostering, client service requests, appointments and
outcomes over a full year of history. The data is entirely synthetic and
deliberately messy -- missing values, duplicate records, orphaned foreign
keys, casing inconsistencies, out-of-range values and a handful of future-
dated errors are injected on purpose so the downstream silver-layer cleaning
and data-quality controls have real work to do.

Run directly with:
    python -m python.ingestion.generate_synthetic_data
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..utils.config import load_yaml, is_dev_mode
from ..utils.logging_config import get_logger
from ..utils.paths import DATA_RAW, DATA_REFERENCE, ensure_dirs

log = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Reference domain content
# --------------------------------------------------------------------------- #

LOCATIONS = [
    ("LOC-01", "Melbourne CBD", "Metro", "Office"),
    ("LOC-02", "Inner North", "Metro", "Community Hub"),
    ("LOC-03", "Inner West", "Metro", "Community Hub"),
    ("LOC-04", "Bayside", "Metro", "Depot"),
    ("LOC-05", "Eastern Suburbs", "Metro", "Community Hub"),
    ("LOC-06", "Northern Growth Corridor", "Growth Area", "Depot"),
    ("LOC-07", "Western Growth Corridor", "Growth Area", "Depot"),
    ("LOC-08", "Geelong / Barwon", "Regional", "Office"),
    ("LOC-09", "Ballarat / Grampians", "Regional", "Office"),
    ("LOC-10", "Bendigo / Loddon", "Regional", "Office"),
]

SKILLS = [
    ("SK-01", "First Aid Certificate", "Safety", True),
    ("SK-02", "Manual Handling", "Safety", True),
    ("SK-03", "Medication Assistance", "Clinical", True),
    ("SK-04", "Dementia Care Specialist", "Clinical", False),
    ("SK-05", "Mental Health First Aid", "Clinical", False),
    ("SK-06", "Complex Care Certification", "Clinical", False),
    ("SK-07", "Driver Licence - Light Vehicle", "Technical", True),
    ("SK-08", "Community Language - Mandarin", "Language", False),
    ("SK-09", "Community Language - Vietnamese", "Language", False),
    ("SK-10", "Community Language - Arabic", "Language", False),
    ("SK-11", "Behaviour Support Practitioner", "Clinical", False),
    ("SK-12", "Allied Health Assistant", "Clinical", False),
    ("SK-13", "Equipment Fitting and Assessment", "Technical", False),
    ("SK-14", "Palliative Care", "Clinical", False),
]

SERVICE_TYPES = [
    # id, name, standard_duration_minutes, requires_skill_id, complexity_weight, category
    ("SVC-01", "In-Home Support Visit", 60, "SK-02", 1.0, "Personal Support"),
    ("SVC-02", "Community Access Outing", 120, "SK-07", 1.2, "Social Support"),
    ("SVC-03", "Nursing Review", 45, "SK-03", 1.6, "Clinical"),
    ("SVC-04", "Equipment Assessment", 60, "SK-13", 1.3, "Clinical"),
    ("SVC-05", "Care Plan Review", 45, None, 1.1, "Coordination"),
    ("SVC-06", "Transport Assistance", 40, "SK-07", 0.8, "Social Support"),
    ("SVC-07", "Allied Health Session", 50, "SK-12", 1.4, "Clinical"),
    ("SVC-08", "Complex Care Visit", 90, "SK-06", 2.0, "Clinical"),
    ("SVC-09", "Behaviour Support Session", 60, "SK-11", 1.8, "Clinical"),
]

COMPLEXITY_TIERS = [
    ("Low", "0-25", "Stable clients with routine, low-risk service needs", 1.0, 1),
    ("Medium", "26-50", "Some clinical or behavioural needs requiring monitoring", 1.25, 2),
    ("High", "51-75", "Multiple co-occurring needs requiring specialist skills", 1.6, 3),
    ("Critical", "76-100", "High-acuity clients requiring senior or specialist staff", 2.1, 3),
]

ROLES = ["Support Worker", "Team Leader", "Coordinator", "Allied Health Clinician", "Registered Nurse"]
EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Casual"]
GENDER_VALUES = ["Female", "Male", "Non-binary / Other"]
AGE_BANDS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
URGENCY_LEVELS = ["Routine", "Priority", "Urgent", "Emergency"]
REQUEST_CHANNELS = ["Phone", "Portal", "Referral", "Case Manager"]
CANCEL_REASONS = ["Client unwell", "Client unavailable", "Staff illness", "Transport issue",
                   "Weather", "Client declined", "Duplicate booking", "Other"]


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _messify_missing(series: pd.Series, rate: float, rng: np.random.Generator) -> pd.Series:
    mask = rng.random(len(series)) < rate
    out = series.copy()
    out[mask] = np.nan
    return out


def _messify_casing(series: pd.Series, rate: float, rng: np.random.Generator) -> pd.Series:
    mask = rng.random(len(series)) < rate
    out = series.astype("object").copy()
    out[mask] = out[mask].astype(str).str.upper()
    return out


# --------------------------------------------------------------------------- #
# Dimension generators
# --------------------------------------------------------------------------- #

def gen_locations() -> pd.DataFrame:
    return pd.DataFrame(LOCATIONS, columns=["location_id", "region_name", "region_type", "site_type"])


def gen_skills() -> pd.DataFrame:
    return pd.DataFrame(SKILLS, columns=["skill_id", "skill_name", "skill_category", "mandatory_flag"])


def gen_service_types() -> pd.DataFrame:
    return pd.DataFrame(SERVICE_TYPES, columns=[
        "service_type_id", "service_type_name", "standard_duration_minutes",
        "requires_skill_id", "complexity_weight", "category"])


def gen_case_complexity() -> pd.DataFrame:
    return pd.DataFrame(COMPLEXITY_TIERS, columns=[
        "complexity_tier", "score_range", "definition", "service_time_multiplier", "min_skill_level"])


def gen_service_level_targets(service_types: pd.DataFrame, locations: pd.DataFrame,
                               rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    tid = 1
    for _, svc in service_types.iterrows():
        for urgency in URGENCY_LEVELS:
            base_hours = {"Emergency": 4, "Urgent": 24, "Priority": 72, "Routine": 168}[urgency]
            for _, loc in locations.iterrows():
                regional_penalty = 1.3 if loc["region_type"] == "Regional" else (1.1 if loc["region_type"] == "Growth Area" else 1.0)
                target_hours = round(base_hours * regional_penalty)
                rows.append({
                    "target_id": f"SLT-{tid:04d}",
                    "service_type_id": svc["service_type_id"],
                    "location_id": loc["location_id"],
                    "urgency": urgency,
                    "target_response_hours": target_hours,
                    "target_completion_days": max(1, round(target_hours / 24)),
                    "min_sla_percent": 95 if urgency in ("Emergency", "Urgent") else 90,
                })
                tid += 1
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# Employees, skills, availability, leave
# --------------------------------------------------------------------------- #

def gen_employees(n: int, locations: pd.DataFrame, rng: np.random.Generator,
                   start_date: pd.Timestamp) -> pd.DataFrame:
    loc_ids = locations["location_id"].values
    rows = []
    for i in range(1, n + 1):
        eid = f"EMP-{i:05d}"
        role = rng.choice(ROLES, p=[0.62, 0.12, 0.10, 0.10, 0.06])
        employment_type = rng.choice(EMPLOYMENT_TYPES, p=[0.42, 0.38, 0.20])
        contracted_hours = {"Full-time": 38, "Part-time": float(rng.choice([16, 20, 24, 30])),
                             "Casual": float(rng.choice([8, 12, 16]))}[employment_type]
        fte = round(contracted_hours / 38, 2)
        hire_days_ago = int(rng.integers(30, 2600))
        hire_date = start_date - pd.Timedelta(days=hire_days_ago)
        status = rng.choice(["Active", "Active", "Active", "Active", "On Leave", "Terminated"])
        rows.append({
            "employee_id": eid,
            "primary_role": role,
            "employment_type": employment_type,
            "contracted_hours_per_week": contracted_hours,
            "fte": fte,
            "base_location_id": rng.choice(loc_ids),
            "hire_date": hire_date.date().isoformat(),
            "employment_status": status,
            "manager_id": None,
            "gender": rng.choice(GENDER_VALUES, p=[0.63, 0.34, 0.03]),
            "age_band": rng.choice(AGE_BANDS, p=[0.10, 0.22, 0.24, 0.22, 0.15, 0.07]),
            "hourly_rate_band": rng.choice(["Band 1", "Band 2", "Band 3", "Band 4"], p=[0.35, 0.35, 0.20, 0.10]),
        })
    df = pd.DataFrame(rows)
    # Assign ~1 manager per 8 staff, from Team Leader/Coordinator roles
    leaders = df[df["primary_role"].isin(["Team Leader", "Coordinator"])]["employee_id"].tolist()
    if leaders:
        df["manager_id"] = [rng.choice(leaders) if eid not in leaders else None for eid in df["employee_id"]]
    # Inject messiness
    df["hourly_rate_band"] = _messify_missing(df["hourly_rate_band"], 0.02, rng)
    df["base_location_id"] = _messify_casing(df["base_location_id"], 0.015, rng)
    # A handful of duplicate employee rows (data-quality issue for silver layer to dedupe)
    dup_idx = rng.choice(df.index, size=max(1, int(len(df) * 0.006)), replace=False)
    dup_rows = df.loc[dup_idx].copy()
    df = pd.concat([df, dup_rows], ignore_index=True)
    return df


def gen_employee_skills(employees: pd.DataFrame, skills: pd.DataFrame, rng: np.random.Generator,
                         start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    rows = []
    skill_ids = skills["skill_id"].values
    mandatory_ids = skills[skills["mandatory_flag"]]["skill_id"].tolist()
    for eid in employees["employee_id"].unique():
        n_skills = int(rng.integers(3, 6))
        chosen = set(mandatory_ids[:2])
        chosen |= set(rng.choice(skill_ids, size=n_skills, replace=False))
        for sid in chosen:
            cert_days_ago = int(rng.integers(10, 1400))
            cert_date = start_date - pd.Timedelta(days=cert_days_ago)
            expiry = cert_date + pd.Timedelta(days=int(rng.choice([365, 730, 1095, 100000])))
            rows.append({
                "employee_id": eid,
                "skill_id": sid,
                "proficiency_level": int(rng.integers(1, 4)),
                "certified_date": cert_date.date().isoformat(),
                "expiry_date": expiry.date().isoformat() if expiry.year < 2100 else None,
            })
    df = pd.DataFrame(rows)
    df["expired_flag"] = pd.to_datetime(df["expiry_date"], errors="coerce") < end_date
    return df


def gen_availability(employees: pd.DataFrame, rng: np.random.Generator, n_exceptions: int,
                      start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    rows = []
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for eid in employees["employee_id"].unique():
        working_days = rng.choice(days, size=int(rng.integers(3, 6)), replace=False)
        for d in days:
            available = d in working_days
            rows.append({
                "employee_id": eid, "pattern_type": "Recurring", "specific_date": None,
                "day_of_week": d, "available_flag": available,
                "earliest_start": "07:00" if available else None,
                "latest_end": rng.choice(["15:00", "17:00", "19:00", "21:00"]) if available else None,
                "preferred_shift_type": rng.choice(["AM", "PM", "Night", "Split"]) if available else None,
            })
    recurring = pd.DataFrame(rows)
    # Date-specific exceptions (e.g. temporary unavailability)
    exc_rows = []
    eids = employees["employee_id"].unique()
    span_days = (end_date - start_date).days
    for _ in range(n_exceptions):
        eid = rng.choice(eids)
        d = start_date + pd.Timedelta(days=int(rng.integers(0, span_days)))
        exc_rows.append({
            "employee_id": eid, "pattern_type": "Exception", "specific_date": d.date().isoformat(),
            "day_of_week": d.day_name(), "available_flag": False,
            "earliest_start": None, "latest_end": None, "preferred_shift_type": None,
        })
    exceptions = pd.DataFrame(exc_rows)
    return pd.concat([recurring, exceptions], ignore_index=True)


def gen_leave(employees: pd.DataFrame, rng: np.random.Generator, n_records: int,
              start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    eids = employees["employee_id"].unique()
    leave_types = ["Annual", "Personal / Carer's", "Sick", "Unpaid", "Parental"]
    span_days = (end_date - start_date).days
    rows = []
    for i in range(n_records):
        eid = rng.choice(eids)
        ltype = rng.choice(leave_types, p=[0.45, 0.22, 0.20, 0.08, 0.05])
        s = start_date + pd.Timedelta(days=int(rng.integers(0, span_days)))
        duration = int(rng.integers(1, 3)) if ltype == "Sick" else int(rng.integers(1, 15))
        e = s + pd.Timedelta(days=duration)
        status = rng.choice(["Approved", "Approved", "Approved", "Pending", "Rejected", "Cancelled"])
        rows.append({
            "leave_id": f"LV-{i+1:05d}", "employee_id": eid, "leave_type": ltype,
            "start_date": s.date().isoformat(), "end_date": e.date().isoformat(),
            "status": status, "approved_by": None if status != "Approved" else "system-approval-workflow",
            "requested_date": (s - pd.Timedelta(days=int(rng.integers(0, 21)))).date().isoformat(),
        })
    df = pd.DataFrame(rows)
    df["leave_type"] = _messify_casing(df["leave_type"], 0.02, rng)
    return df


# --------------------------------------------------------------------------- #
# Clients, service requests, appointments, waiting times, cancellations, outcomes
# --------------------------------------------------------------------------- #

def gen_clients(n: int, locations: pd.DataFrame, rng: np.random.Generator,
                 start_date: pd.Timestamp) -> pd.DataFrame:
    loc_ids = locations["location_id"].values
    languages = ["English", "Mandarin", "Vietnamese", "Arabic", "Greek", "Italian", "Other"]
    rows = []
    for i in range(1, n + 1):
        tier = rng.choice(["Low", "Medium", "High", "Critical"], p=[0.40, 0.33, 0.20, 0.07])
        since_days_ago = int(rng.integers(30, 2200))
        rows.append({
            "client_id": f"CLT-{i:05d}",
            "location_id": rng.choice(loc_ids),
            "client_since_date": (start_date - pd.Timedelta(days=since_days_ago)).date().isoformat(),
            "complexity_tier": tier,
            "preferred_language": rng.choice(languages, p=[0.68, 0.06, 0.06, 0.05, 0.05, 0.04, 0.06]),
            "active_flag": rng.choice([True, True, True, False], p=[0.7, 0.15, 0.1, 0.05]),
            "consent_data_use_flag": rng.choice([True, False], p=[0.97, 0.03]),
            "communication_preference": rng.choice(["Phone", "Email", "SMS", "Post"], p=[0.5, 0.3, 0.15, 0.05]),
        })
    df = pd.DataFrame(rows)
    df["preferred_language"] = _messify_missing(df["preferred_language"], 0.02, rng)
    return df


def gen_service_requests(clients: pd.DataFrame, service_types: pd.DataFrame, locations: pd.DataFrame,
                          rng: np.random.Generator, start_date: pd.Timestamp, end_date: pd.Timestamp,
                          avg_per_day: float) -> pd.DataFrame:
    tier_score = {"Low": (5, 25), "Medium": (26, 50), "High": (51, 75), "Critical": (76, 97)}
    client_lookup = clients.set_index("client_id")
    svc_ids = service_types["service_type_id"].values
    dates = pd.date_range(start_date, end_date, freq="D")
    rows = []
    rid = 1
    for d in dates:
        dow = d.dayofweek  # 0=Mon
        weekday_factor = 1.25 if dow < 5 else 0.55
        # Winter (Jun-Aug, southern hemisphere) demand uplift for a community-services org
        month = d.month
        seasonal_factor = 1.20 if month in (6, 7, 8) else (1.08 if month in (5, 9) else 1.0)
        # gentle organic growth across the year
        growth_factor = 1.0 + 0.18 * ((d - start_date).days / max(1, (end_date - start_date).days))
        lam = avg_per_day * weekday_factor * seasonal_factor * growth_factor
        n_today = rng.poisson(lam)
        for _ in range(n_today):
            client_id = rng.choice(clients["client_id"].values)
            tier = client_lookup.loc[client_id, "complexity_tier"]
            lo, hi = tier_score[tier]
            complexity_score = float(np.clip(rng.normal((lo + hi) / 2, 6), 1, 99))
            svc = rng.choice(svc_ids, p=_svc_probs(service_types, rng))
            urgency = rng.choice(URGENCY_LEVELS, p=_urgency_probs(tier))
            requested_by = rng.choice(["Client", "Family Member", "Case Manager", "GP / Clinician"],
                                       p=_requested_by_probs(tier))
            channel = rng.choice(REQUEST_CHANNELS, p=_channel_probs(tier))
            region_id = client_lookup.loc[client_id, "location_id"]
            rows.append({
                "request_id": f"REQ-{rid:06d}",
                "client_id": client_id,
                "service_type_id": svc,
                "location_id": region_id,
                "requested_date": d.date().isoformat(),
                "requested_by": requested_by,
                "urgency": urgency,
                "complexity_score": round(complexity_score, 1),
                "requested_channel": channel,
                "status": None,  # resolved later once appointments are generated
            })
            rid += 1
    df = pd.DataFrame(rows)
    # A few requests reference a client_id that does not exist (orphan FK, e.g. archived client)
    orphan_n = max(1, int(len(df) * 0.004))
    orphan_idx = rng.choice(df.index, size=orphan_n, replace=False)
    df.loc[orphan_idx, "client_id"] = [f"CLT-{90000 + i}" for i in range(orphan_n)]
    # Missing complexity score on a slice of records
    df["complexity_score"] = _messify_missing(df["complexity_score"], 0.03, rng)
    return df


def _svc_probs(service_types: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    base = np.array([0.22, 0.14, 0.10, 0.08, 0.14, 0.10, 0.10, 0.06, 0.06])
    return base / base.sum()


def _urgency_probs(tier: str) -> list[float]:
    return {
        "Low":      [0.70, 0.22, 0.07, 0.01],
        "Medium":   [0.50, 0.32, 0.15, 0.03],
        "High":     [0.30, 0.35, 0.28, 0.07],
        "Critical": [0.12, 0.28, 0.40, 0.20],
    }[tier]


def _requested_by_probs(tier: str) -> list[float]:
    # order: Client, Family Member, Case Manager, GP / Clinician
    return {
        "Low":      [0.62, 0.24, 0.11, 0.03],
        "Medium":   [0.42, 0.28, 0.22, 0.08],
        "High":     [0.22, 0.28, 0.34, 0.16],
        "Critical": [0.10, 0.22, 0.38, 0.30],
    }[tier]


def _channel_probs(tier: str) -> list[float]:
    # order matches REQUEST_CHANNELS: Phone, Portal, Referral, Case Manager
    return {
        "Low":      [0.32, 0.44, 0.14, 0.10],
        "Medium":   [0.38, 0.32, 0.18, 0.12],
        "High":     [0.44, 0.18, 0.24, 0.14],
        "Critical": [0.48, 0.08, 0.30, 0.14],
    }[tier]


def location_pressure_factors(locations: pd.DataFrame, rng: np.random.Generator) -> dict:
    """Fixed per-region capacity-pressure multiplier: growth corridors and regional
    sites are structurally tighter-staffed than established metro sites. This is the
    single source of regional heterogeneity that the overtime, waiting-time and
    SLA-breach generators below all draw on, so a region that is under pressure
    shows up consistently across overtime, wait times and breach risk -- which is
    exactly the kind of cross-metric pattern a capacity-gap model should learn."""
    base = {"Metro": 0.95, "Growth Area": 1.30, "Regional": 1.20}
    out = {}
    for _, loc in locations.iterrows():
        jitter = rng.uniform(-0.08, 0.08)
        out[loc["location_id"]] = round(base[loc["region_type"]] + jitter, 3)
    return out


def gen_shifts(employees: pd.DataFrame, locations: pd.DataFrame, leave: pd.DataFrame,
               rng: np.random.Generator, start_date: pd.Timestamp, end_date: pd.Timestamp,
               pressure: dict) -> pd.DataFrame:
    active = employees[employees["employment_status"] == "Active"].drop_duplicates("employee_id")
    dates = pd.date_range(start_date, end_date, freq="D")
    leave_by_emp: dict[str, list[tuple]] = {}
    for _, lv in leave[leave["status"] == "Approved"].iterrows():
        leave_by_emp.setdefault(lv["employee_id"], []).append(
            (pd.Timestamp(lv["start_date"]), pd.Timestamp(lv["end_date"])))

    def on_leave(eid: str, day: pd.Timestamp) -> bool:
        for s, e in leave_by_emp.get(eid, []):
            if s <= day <= e:
                return True
        return False

    shift_types = {"AM": ("07:00", "15:00"), "PM": ("13:00", "21:00"),
                   "Night": ("21:00", "07:00"), "Split": ("07:00", "19:00")}
    rows = []
    sid = 1
    for _, emp in active.iterrows():
        eid = emp["employee_id"]
        days_per_week = {"Full-time": 5, "Part-time": int(rng.integers(2, 4)), "Casual": int(rng.integers(1, 3))}[emp["employment_type"]]
        work_days = set(rng.choice(range(7), size=min(days_per_week, 7), replace=False))
        for d in dates:
            if d.dayofweek not in work_days:
                continue
            if on_leave(eid, d):
                continue
            if rng.random() < 0.03:  # unplanned absence not tied to formal leave record
                continue
            stype = rng.choice(list(shift_types.keys()), p=[0.45, 0.35, 0.10, 0.10])
            start_str, end_str = shift_types[stype]
            planned_hours = 8.0 if stype != "Split" else 10.0
            loc_id = emp["base_location_id"] if isinstance(emp["base_location_id"], str) else None
            dow_factor = 1.25 if d.dayofweek in (0, 1, 2) else (0.85 if d.dayofweek == 4 else 1.0)
            winter_factor = 1.15 if d.month in (6, 7, 8) else 1.0
            p_overtime = np.clip(0.09 * pressure.get(loc_id, 1.0) * dow_factor * winter_factor, 0.02, 0.42)
            is_overtime = rng.random() < p_overtime
            actual_hours = planned_hours + (rng.uniform(0.5, 3.0) if is_overtime else rng.normal(0, 0.15))
            actual_hours = max(0.5, actual_hours)
            status = rng.choice(["Completed", "Completed", "Completed", "Cancelled", "No-show"], p=[0.90, 0.05, 0.02, 0.02, 0.01])
            rows.append({
                "shift_id": f"SFT-{sid:06d}", "employee_id": eid,
                "shift_date": d.date().isoformat(),
                "location_id": loc_id,
                "shift_type": stype,
                "planned_start": start_str, "planned_end": end_str,
                "planned_hours": planned_hours,
                "actual_hours": round(actual_hours, 2) if status == "Completed" else 0.0,
                "status": status,
                "is_overtime_flag": bool(is_overtime and status == "Completed"),
            })
            sid += 1
    df = pd.DataFrame(rows)
    df["location_id"] = _messify_casing(df["location_id"], 0.02, rng)
    return df


def gen_appointments_and_related(service_requests: pd.DataFrame, employees: pd.DataFrame,
                                  employee_skills: pd.DataFrame, service_types: pd.DataFrame,
                                  service_level_targets: pd.DataFrame, rng: np.random.Generator,
                                  pressure: dict):
    active_emp = employees[employees["employment_status"] == "Active"].drop_duplicates("employee_id")
    emp_ids = active_emp["employee_id"].values
    svt_lookup = service_level_targets.set_index(["service_type_id", "location_id", "urgency"])

    appt_rows, wait_rows, cancel_rows, outcome_rows = [], [], [], []
    aid = cid = oid = 1

    for _, req in service_requests.iterrows():
        # ~6% of requests remain an open backlog item with no appointment yet
        if rng.random() < 0.06:
            continue
        requested_date = pd.Timestamp(req["requested_date"])
        urgency = req["urgency"]
        complexity = req["complexity_score"] if pd.notna(req["complexity_score"]) else 30.0
        loc_pressure = pressure.get(req["location_id"], 1.0)
        # Waiting time has a genuine, learnable structure: regional capacity pressure
        # and case complexity both push wait times out; urgency triages some of that
        # away but does not cancel it, so breach risk still varies meaningfully by
        # region and complexity even after conditioning on urgency (a realistic
        # operational pattern, and the signal the SLA-breach model is trained to find).
        urgency_speed = {"Emergency": 0.35, "Urgent": 0.55, "Priority": 0.85, "Routine": 1.15}.get(urgency, 1.0)
        complexity_factor = 0.7 + (complexity / 100) * 0.9
        base_scale_hours = 30.0 * loc_pressure * complexity_factor * urgency_speed
        wait_hours = max(0.5, rng.gamma(shape=2.2, scale=base_scale_hours / 2.2))
        scheduled_dt = requested_date + pd.Timedelta(hours=wait_hours)
        travel_minutes = max(3, int(rng.normal(22, 12) * loc_pressure))

        # Cancellation / no-show risk: lower for urgent-tier requests (higher stakes),
        # higher with longer travel, higher on Mondays/Fridays, higher for very long waits,
        # and varies by service type (transport-dependent services are more exposed to
        # weather/logistics disruption). Effect sizes are deliberately large enough to be
        # learnable by the cancellation-prediction model above sampling noise.
        dow = scheduled_dt.dayofweek
        svc_cancel_bias = {"SVC-02": 0.15, "SVC-06": 0.12, "SVC-08": -0.07, "SVC-09": -0.06}.get(req["service_type_id"], 0.0)
        p_cancel = 0.10
        p_cancel += {"Emergency": -0.12, "Urgent": -0.06, "Priority": 0.04, "Routine": 0.14}.get(urgency, 0.0)
        p_cancel += 0.10 if dow in (0, 4) else -0.04
        p_cancel += 0.15 if wait_hours > 200 else (0.07 if wait_hours > 100 else 0.0)
        p_cancel += 0.08 if complexity > 70 else (0.04 if complexity > 50 else 0.0)
        p_cancel += svc_cancel_bias
        p_cancel += 0.10 if travel_minutes > 35 else 0.0
        p_cancel = float(np.clip(p_cancel, 0.02, 0.6))
        p_noshow = p_cancel * 0.35
        p_reschedule = 0.06
        roll = rng.random()
        if roll < p_cancel:
            appt_status = "Cancelled"
        elif roll < p_cancel + p_noshow:
            appt_status = "No-show"
        elif roll < p_cancel + p_noshow + p_reschedule:
            appt_status = "Rescheduled"
        else:
            appt_status = "Completed"

        employee_id = rng.choice(emp_ids)
        override_flag = rng.random() < 0.05
        appt_rows.append({
            "appointment_id": f"APT-{aid:06d}", "request_id": req["request_id"],
            "employee_id": employee_id, "location_id": req["location_id"],
            "service_type_id": req["service_type_id"],
            "scheduled_date": scheduled_dt.date().isoformat(),
            "scheduled_start": f"{int(rng.integers(7,17)):02d}:{rng.choice(['00','15','30','45'])}",
            "status": appt_status,
            "travel_minutes": travel_minutes,
            "override_flag": override_flag,
            "override_reason": rng.choice(["Client preference", "Skill match unavailable", "Continuity of care", "Urgent reassignment"]) if override_flag else None,
        })

        sla_key = (req["service_type_id"], req["location_id"], urgency)
        default_target_hours = {"Emergency": 4, "Urgent": 24, "Priority": 72, "Routine": 168}.get(urgency, 168)
        sla_target_hours = svt_lookup.loc[sla_key, "target_response_hours"] if sla_key in svt_lookup.index else default_target_hours
        sla_met = wait_hours <= sla_target_hours
        wait_rows.append({
            "request_id": req["request_id"],
            "requested_date": req["requested_date"],
            "scheduled_date": scheduled_dt.date().isoformat(),
            "completed_date": scheduled_dt.date().isoformat() if appt_status == "Completed" else None,
            "waiting_hours_to_schedule": round(wait_hours, 1),
            "waiting_days_to_schedule": round(wait_hours / 24, 2),
            "sla_target_hours": sla_target_hours,
            "sla_met_flag": bool(sla_met),
        })

        if appt_status in ("Cancelled", "No-show"):
            notice_hours = max(0, rng.normal(18, 20))
            cancel_rows.append({
                "cancellation_id": f"CAN-{cid:05d}", "appointment_id": f"APT-{aid:06d}",
                "cancelled_by": rng.choice(["Client", "Employee", "Organisation"], p=[0.55, 0.25, 0.20]),
                "cancellation_reason": rng.choice(CANCEL_REASONS),
                "notice_hours": round(notice_hours, 1),
                "rebooked_flag": rng.choice([True, False], p=[0.65, 0.35]),
            })
            cid += 1

        if appt_status == "Completed":
            satisfaction = float(np.clip(rng.normal(4.2, 0.7), 1, 5))
            quality = float(np.clip(rng.normal(82, 10), 20, 100))
            incident = rng.random() < 0.018
            outcome_rows.append({
                "outcome_id": f"OUT-{oid:06d}", "appointment_id": f"APT-{aid:06d}",
                "client_satisfaction_score": round(satisfaction, 1),
                "outcome_quality_score": round(quality, 1),
                "incident_flag": bool(incident),
                "incident_severity": rng.choice(["Low", "Medium", "High"]) if incident else None,
                "goal_achieved_flag": rng.choice([True, False], p=[0.86, 0.14]),
                "follow_up_required_flag": rng.choice([True, False], p=[0.22, 0.78]),
            })
            oid += 1
        aid += 1

    appointments = pd.DataFrame(appt_rows)
    waiting_times = pd.DataFrame(wait_rows)
    cancellations = pd.DataFrame(cancel_rows)
    outcomes = pd.DataFrame(outcome_rows)

    # Messiness: some satisfaction scores missing (client declined to answer)
    if len(outcomes):
        outcomes["client_satisfaction_score"] = _messify_missing(outcomes["client_satisfaction_score"], 0.08, rng)
    return appointments, waiting_times, cancellations, outcomes


def gen_overtime(shifts: pd.DataFrame, locations: pd.DataFrame, employees: pd.DataFrame) -> pd.DataFrame:
    df = shifts.copy()
    df["shift_date"] = pd.to_datetime(df["shift_date"])
    df["week_start_date"] = df["shift_date"] - pd.to_timedelta(df["shift_date"].dt.dayofweek, unit="D")
    completed = df[df["status"] == "Completed"]
    grouped = completed.groupby(["employee_id", "week_start_date"], as_index=False).agg(
        rostered_hours=("planned_hours", "sum"),
        actual_hours_worked=("actual_hours", "sum"),
    )
    contracted = employees.drop_duplicates("employee_id").set_index("employee_id")["contracted_hours_per_week"]
    grouped["contracted_hours"] = grouped["employee_id"].map(contracted).fillna(38)
    grouped["overtime_hours"] = (grouped["actual_hours_worked"] - grouped["contracted_hours"]).clip(lower=0).round(2)
    grouped["overtime_approved_flag"] = grouped["overtime_hours"].apply(lambda h: bool(h > 0) and np.random.default_rng(int(h * 1000) % 9999).random() < 0.9)
    grouped["week_start_date"] = grouped["week_start_date"].dt.date.astype(str)
    return grouped


def resolve_request_status(service_requests: pd.DataFrame, appointments: pd.DataFrame) -> pd.DataFrame:
    appt_by_req = appointments.set_index("request_id")["status"] if len(appointments) else pd.Series(dtype=object)
    df = service_requests.copy()

    def status_for(rid: str) -> str:
        if rid not in appt_by_req.index:
            return "Backlog"
        s = appt_by_req.loc[rid]
        if isinstance(s, pd.Series):
            s = s.iloc[0]
        return {"Completed": "Completed", "Cancelled": "Cancelled", "No-show": "Cancelled",
                "Rescheduled": "Scheduled"}.get(s, "Scheduled")

    df["status"] = df["request_id"].apply(status_for)
    return df


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def run(dev_mode: bool | None = None) -> dict[str, int]:
    ensure_dirs()
    cfg = load_yaml("data_generation.yml")
    dev_mode = is_dev_mode() if dev_mode is None else dev_mode
    p = cfg["dev_mode"]
    seed = cfg["random_seed"]
    rng = _rng(seed)
    start_date = pd.Timestamp(cfg["horizon"]["start_date"])
    end_date = pd.Timestamp(cfg["horizon"]["end_date"])

    log.info("Generating synthetic workforce and service-demand data (dev_mode=%s, seed=%s)", dev_mode, seed)

    locations = gen_locations()
    skills = gen_skills()
    service_types = gen_service_types()
    case_complexity = gen_case_complexity()
    service_level_targets = gen_service_level_targets(service_types, locations, rng)

    employees = gen_employees(p["n_employees"], locations, rng, start_date)
    employee_skills = gen_employee_skills(employees, skills, rng, start_date, end_date)
    availability = gen_availability(employees, rng, p["target_availability_exceptions"], start_date, end_date)
    leave = gen_leave(employees, rng, p["target_leave_records"], start_date, end_date)

    pressure = location_pressure_factors(locations, rng)

    clients = gen_clients(p["n_clients"], locations, rng, start_date)
    service_requests = gen_service_requests(clients, service_types, locations, rng, start_date, end_date, p["avg_requests_per_day"])

    shifts = gen_shifts(employees, locations, leave, rng, start_date, end_date, pressure)
    overtime = gen_overtime(shifts, locations, employees)

    appointments, waiting_times, cancellations, outcomes = gen_appointments_and_related(
        service_requests, employees, employee_skills, service_types, service_level_targets, rng, pressure)
    service_requests = resolve_request_status(service_requests, appointments)

    tables = {
        "locations": locations, "skills": skills, "service_types": service_types,
        "case_complexity": case_complexity, "service_level_targets": service_level_targets,
        "employees": employees, "employee_skills": employee_skills, "availability": availability,
        "leave": leave, "clients": clients, "service_requests": service_requests,
        "shifts": shifts, "overtime": overtime, "appointments": appointments,
        "waiting_times": waiting_times, "cancellations": cancellations, "outcomes": outcomes,
    }

    counts = {}
    for name, df in tables.items():
        dest = DATA_REFERENCE if name in ("locations", "skills", "service_types", "case_complexity", "service_level_targets") else DATA_RAW
        out_path = dest / f"{name}.csv"
        df.to_csv(out_path, index=False)
        counts[name] = len(df)
        log.info("  wrote %-24s %6d rows -> %s", name, len(df), out_path.relative_to(out_path.parents[2]))

    return counts


if __name__ == "__main__":
    result = run()
    total = sum(result.values())
    print(f"Generated {len(result)} synthetic datasets, {total:,} total rows.")
    for k, v in result.items():
        print(f"  {k:24s} {v:8,d}")
