#!/usr/bin/env python3
"""
Sentinel — Phase 1: Point-in-time feature engineering.

Reads the immutable raw_events.csv and produces features.csv.

CRITICAL INVARIANT:
    For every transaction at time T, every derived feature uses ONLY
    information available strictly before T. The current transaction is
    never included in its own historical statistics or velocity counts.
    Future transactions can never affect earlier features.

The raw dataset is never modified.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Deque, Dict, List, Tuple

EARTH_RADIUS_KM = 6371.0
DEFAULT_VELOCITY_WINDOW_MIN = 5
VELOCITY_1H_MIN = 60
FAILED_VELOCITY_MIN = 60


def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def load_raw(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["timestamp"] = parse_ts(r["timestamp"])
            r["account_creation_timestamp"] = parse_ts(r["account_creation_timestamp"])
            r["transaction_amount"] = float(r["transaction_amount"])
            r["latitude"] = float(r["latitude"])
            r["longitude"] = float(r["longitude"])
            r["payment_attempt_number"] = int(r["payment_attempt_number"])
            r["is_fraud"] = r["is_fraud"].strip().lower() == "true"
            rows.append(r)
    # Defensive: ensure chronological order (raw is already sorted, but we
    # must not rely on that for correctness).
    rows.sort(key=lambda r: (r["timestamp"], r["transaction_id"]))
    return rows


def engineer(rows: List[Dict], velocity_window_min: int) -> Tuple[List[Dict], Dict]:
    """
    Iterate transactions in chronological order, maintaining per-entity state
    that is updated ONLY AFTER each transaction's features are computed.

    State structures:
        user_history[user]   = deque of (ts, amount, status)   — kept bounded to last 24h
        user_devices[user]   = set of device_fingerprint seen so far
        user_ips[user]       = set of ip_address seen so far
        user_last_loc[user]  = (ts, lat, lon) of most recent transaction
        user_failed[user]    = deque of failed-status timestamps (bounded)
        device_users[device] = set of user_ids seen so far
        ip_users[ip]         = set of user_ids seen so far
    """
    user_history: Dict[str, Deque[Tuple[datetime, float, str]]] = defaultdict(deque)
    user_devices: Dict[str, set] = defaultdict(set)
    user_ips: Dict[str, set] = defaultdict(set)
    user_last_loc: Dict[str, Tuple[datetime, float, float]] = {}
    user_failed: Dict[str, Deque[datetime]] = defaultdict(deque)
    device_users: Dict[str, set] = defaultdict(set)
    ip_users: Dict[str, set] = defaultdict(set)

    velocity_field = f"transaction_velocity_{velocity_window_min}m"
    velocity_window = timedelta(minutes=velocity_window_min)
    one_hour = timedelta(minutes=VELOCITY_1H_MIN)
    failed_window = timedelta(minutes=FAILED_VELOCITY_MIN)
    prune_window = timedelta(hours=24)  # for bounding deque sizes

    feature_rows: List[Dict] = []

    for r in rows:
        user = r["user_id"]
        device = r["device_fingerprint"]
        ip = r["ip_address"]
        ts = r["timestamp"]
        amount = r["transaction_amount"]
        status = r["transaction_status"]
        lat = r["latitude"]
        lon = r["longitude"]

        hist = user_history[user]
        hist_count = len(hist)

        # --- Cold-start flags ---
        is_first = hist_count == 0
        has_hist_amount = hist_count > 0
        has_prev_loc = user in user_last_loc

        # --- Historical amount features (strictly previous transactions) ---
        if has_hist_amount:
            amounts_so_far = [h[1] for h in hist]
            hist_avg_amount = sum(amounts_so_far) / len(amounts_so_far)
            amount_ratio = amount / hist_avg_amount if hist_avg_amount > 0 else None
        else:
            hist_avg_amount = None
            amount_ratio = None

        # --- Velocity windows (strictly before current ts) ---
        # Prune deque to keep only last 24h for memory efficiency.
        cutoff_prune = ts - prune_window
        while hist and hist[0][0] < cutoff_prune:
            hist.popleft()

        cutoff_v_short = ts - velocity_window
        cutoff_v_1h = ts - one_hour
        vel_short = 0
        vel_1h = 0
        for h_ts, _h_amt, _h_status in hist:
            if h_ts >= cutoff_v_short:
                vel_short += 1
            if h_ts >= cutoff_v_1h:
                vel_1h += 1

        # --- Time since previous transaction ---
        if hist:
            time_since_prev = (ts - hist[-1][0]).total_seconds()
        else:
            time_since_prev = None

        # --- Unique devices / IPs seen before for this user ---
        unique_devices_before = len(user_devices[user])
        unique_ips_before = len(user_ips[user])

        # --- Device / IP user counts (strictly before current) ---
        device_user_count = len(device_users[device])
        ip_user_count = len(ip_users[ip])

        # --- Failed attempt velocity (last 60 min, strictly before current) ---
        failed_deque = user_failed[user]
        cutoff_failed = ts - failed_window
        while failed_deque and failed_deque[0] < cutoff_failed:
            failed_deque.popleft()
        failed_velocity = sum(1 for t in failed_deque if t >= cutoff_failed)

        # --- Geographic features ---
        if has_prev_loc:
            prev_ts, prev_lat, prev_lon = user_last_loc[user]
            geo_distance = haversine_km(prev_lat, prev_lon, lat, lon)
            time_diff_h = (ts - prev_ts).total_seconds() / 3600.0
            if time_diff_h > 0:
                geo_velocity = geo_distance / time_diff_h
            else:
                geo_velocity = None
        else:
            geo_distance = None
            geo_velocity = None

        # --- Time since account creation (raw, safe) ---
        account_age_seconds = (ts - r["account_creation_timestamp"]).total_seconds()

        feature_row = {
            # Raw fields (passed through unchanged)
            "transaction_id": r["transaction_id"],
            "timestamp": r["timestamp"].isoformat(),
            "user_id": r["user_id"],
            "merchant_id": r["merchant_id"],
            "device_fingerprint": r["device_fingerprint"],
            "ip_address": r["ip_address"],
            "payment_method": r["payment_method"],
            "transaction_amount": r["transaction_amount"],
            "currency": r["currency"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "transaction_status": r["transaction_status"],
            "account_creation_timestamp": r["account_creation_timestamp"].isoformat(),
            "payment_attempt_number": r["payment_attempt_number"],
            "transaction_type": r["transaction_type"],
            # Derived features (all point-in-time correct)
            "is_first_transaction": is_first,
            "has_historical_amount": has_hist_amount,
            "has_previous_location": has_prev_loc,
            "historical_transaction_count": hist_count,
            "historical_avg_amount": hist_avg_amount,
            "amount_ratio_to_history": amount_ratio,
            velocity_field: vel_short,
            "transaction_velocity_1h": vel_1h,
            "time_since_previous_transaction": time_since_prev,
            "unique_devices_seen_before": unique_devices_before,
            "unique_ips_seen_before": unique_ips_before,
            "device_user_count": device_user_count,
            "ip_user_count": ip_user_count,
            "failed_attempt_velocity": failed_velocity,
            "geographic_distance_from_previous": geo_distance,
            "geographic_velocity": geo_velocity,
            "account_age_seconds": account_age_seconds,
            # Ground truth (NOT fraud_scenario)
            "is_fraud": r["is_fraud"],
        }
        feature_rows.append(feature_row)

        # --- Update state AFTER computing features for current transaction ---
        hist.append((ts, amount, status))
        user_devices[user].add(device)
        user_ips[user].add(ip)
        user_last_loc[user] = (ts, lat, lon)
        if status == "failed":
            user_failed[user].append(ts)
        device_users[device].add(user)
        ip_users[ip].add(user)

    # Validation summary
    n_rows = len(feature_rows)
    n_features = len([k for k in feature_rows[0].keys() if k not in (
        "transaction_id", "timestamp", "user_id", "merchant_id",
        "device_fingerprint", "ip_address", "payment_method",
        "transaction_amount", "currency", "latitude", "longitude",
        "transaction_status", "account_creation_timestamp",
        "payment_attempt_number", "transaction_type", "is_fraud",
    )])

    n_first = sum(1 for r in feature_rows if r["is_first_transaction"])
    n_with_hist = n_rows - n_first

    missing = {}
    for col in ("historical_avg_amount", "amount_ratio_to_history",
                "time_since_previous_transaction",
                "geographic_distance_from_previous", "geographic_velocity"):
        missing[col] = sum(1 for r in feature_rows if r[col] is None)

    # Velocity stats
    vel_short_vals = [r[velocity_field] for r in feature_rows]
    vel_1h_vals = [r["transaction_velocity_1h"] for r in feature_rows]
    dev_counts = [r["device_user_count"] for r in feature_rows]
    ip_counts = [r["ip_user_count"] for r in feature_rows]
    geo_dists = [r["geographic_distance_from_previous"] for r in feature_rows
                 if r["geographic_distance_from_previous"] is not None]
    geo_vels = [r["geographic_velocity"] for r in feature_rows
                if r["geographic_velocity"] is not None]

    summary = {
        "total_rows": n_rows,
        "feature_columns": n_features,
        "first_transaction_count": n_first,
        "users_with_history_count": n_with_hist,
        "missing_values": missing,
        "velocity_short_window_minutes": velocity_window_min,
        "velocity_stats": {
            "short_window": {
                "field": velocity_field,
                "min": min(vel_short_vals), "max": max(vel_short_vals),
                "mean": sum(vel_short_vals) / n_rows,
                "nonzero_count": sum(1 for v in vel_short_vals if v > 0),
            },
            "1h": {
                "min": min(vel_1h_vals), "max": max(vel_1h_vals),
                "mean": sum(vel_1h_vals) / n_rows,
                "nonzero_count": sum(1 for v in vel_1h_vals if v > 0),
            },
        },
        "device_sharing_stats": {
            "min": min(dev_counts), "max": max(dev_counts),
            "mean": sum(dev_counts) / n_rows,
            "shared_count": sum(1 for v in dev_counts if v > 0),
        },
        "ip_sharing_stats": {
            "min": min(ip_counts), "max": max(ip_counts),
            "mean": sum(ip_counts) / n_rows,
            "shared_count": sum(1 for v in ip_counts if v > 0),
        },
        "geographic_stats": {
            "with_previous_location": len(geo_dists),
            "distance_mean_km": (sum(geo_dists) / len(geo_dists)) if geo_dists else 0,
            "distance_max_km": max(geo_dists) if geo_dists else 0,
            "velocity_mean_kmh": (sum(geo_vels) / len(geo_vels)) if geo_vels else 0,
            "velocity_max_kmh": max(geo_vels) if geo_vels else 0,
        },
    }
    return feature_rows, summary


def write_features(rows: List[Dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            out = dict(r)
            out["is_first_transaction"] = "true" if r["is_first_transaction"] else "false"
            out["has_historical_amount"] = "true" if r["has_historical_amount"] else "false"
            out["has_previous_location"] = "true" if r["has_previous_location"] else "false"
            out["is_fraud"] = "true" if r["is_fraud"] else "false"
            for k in ("historical_avg_amount", "amount_ratio_to_history",
                      "time_since_previous_transaction",
                      "geographic_distance_from_previous", "geographic_velocity"):
                if out[k] is None:
                    out[k] = ""
            writer.writerow(out)


def write_metadata(path: Path, velocity_window_min: int) -> None:
    meta = {
        "transaction_id": {
            "description": "Opaque UUID transaction identifier.",
            "dtype": "string", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "timestamp": {
            "description": "ISO-8601 UTC transaction timestamp.",
            "dtype": "datetime", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "user_id": {
            "description": "Opaque user identifier.",
            "dtype": "string", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "merchant_id": {
            "description": "Opaque merchant identifier.",
            "dtype": "string", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "device_fingerprint": {
            "description": "Opaque device fingerprint.",
            "dtype": "string", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "ip_address": {
            "description": "IPv4 address (opaque).",
            "dtype": "string", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "payment_method": {
            "description": "Payment instrument type.",
            "dtype": "categorical", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "transaction_amount": {
            "description": "Transaction amount in the given currency.",
            "dtype": "float", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "currency": {
            "description": "ISO currency code.",
            "dtype": "categorical", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "latitude": {
            "description": "Latitude of the transaction origin.",
            "dtype": "float", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "longitude": {
            "description": "Longitude of the transaction origin.",
            "dtype": "float", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "transaction_status": {
            "description": "Terminal status: success / failed / pending.",
            "dtype": "categorical", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "account_creation_timestamp": {
            "description": "ISO-8601 UTC account creation time.",
            "dtype": "datetime", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "payment_attempt_number": {
            "description": "Attempt index for this payment (1-based).",
            "dtype": "int", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "transaction_type": {
            "description": "Transaction type: purchase / refund / topup / transfer.",
            "dtype": "categorical", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "is_first_transaction": {
            "description": "True if this is the user's first ever transaction.",
            "dtype": "bool", "uses_future_data": False,
            "historical": True, "can_be_missing": False,
        },
        "has_historical_amount": {
            "description": "True if user has any prior transaction amount.",
            "dtype": "bool", "uses_future_data": False,
            "historical": True, "can_be_missing": False,
        },
        "has_previous_location": {
            "description": "True if user has a prior known location.",
            "dtype": "bool", "uses_future_data": False,
            "historical": True, "can_be_missing": False,
        },
        "historical_transaction_count": {
            "description": "Number of prior transactions by the user.",
            "dtype": "int", "uses_future_data": False,
            "historical": True, "can_be_missing": False,
        },
        "historical_avg_amount": {
            "description": "Mean amount of prior transactions for the user.",
            "dtype": "float", "uses_future_data": False,
            "historical": True, "can_be_missing": True,
        },
        "amount_ratio_to_history": {
            "description": "current_amount / historical_avg_amount (None if no history).",
            "dtype": "float", "uses_future_data": False,
            "historical": True, "can_be_missing": True,
        },
        f"transaction_velocity_{velocity_window_min}m": {
            "description": f"Number of prior transactions by the user within the previous {velocity_window_min} minutes.",
            "dtype": "int", "uses_future_data": False,
            "historical": True, "can_be_missing": False,
            "calculation_window_minutes": velocity_window_min,
        },
        "transaction_velocity_1h": {
            "description": "Number of prior transactions by the user within the previous 60 minutes.",
            "dtype": "int", "uses_future_data": False,
            "historical": True, "can_be_missing": False,
            "calculation_window_minutes": 60,
        },
        "time_since_previous_transaction": {
            "description": "Seconds since the user's previous transaction (None if first).",
            "dtype": "float", "uses_future_data": False,
            "historical": True, "can_be_missing": True,
        },
        "unique_devices_seen_before": {
            "description": "Distinct devices the user has used in prior transactions.",
            "dtype": "int", "uses_future_data": False,
            "historical": True, "can_be_missing": False,
        },
        "unique_ips_seen_before": {
            "description": "Distinct IPs the user has used in prior transactions.",
            "dtype": "int", "uses_future_data": False,
            "historical": True, "can_be_missing": False,
        },
        "device_user_count": {
            "description": "Distinct users observed on this device in prior transactions.",
            "dtype": "int", "uses_future_data": False,
            "historical": True, "can_be_missing": False,
        },
        "ip_user_count": {
            "description": "Distinct users observed on this IP in prior transactions.",
            "dtype": "int", "uses_future_data": False,
            "historical": True, "can_be_missing": False,
        },
        "failed_attempt_velocity": {
            "description": "Number of prior failed transactions by the user in the last 60 minutes.",
            "dtype": "int", "uses_future_data": False,
            "historical": True, "can_be_missing": False,
            "calculation_window_minutes": 60,
        },
        "geographic_distance_from_previous": {
            "description": "Km from the user's previous transaction location (None if first).",
            "dtype": "float", "uses_future_data": False,
            "historical": True, "can_be_missing": True,
        },
        "geographic_velocity": {
            "description": "Implied travel speed (km/h) from previous transaction location.",
            "dtype": "float", "uses_future_data": False,
            "historical": True, "can_be_missing": True,
        },
        "account_age_seconds": {
            "description": "Seconds between account creation and transaction time.",
            "dtype": "float", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "is_fraud": {
            "description": "Ground-truth fraud label. Not derived from the model.",
            "dtype": "bool", "uses_future_data": False,
            "historical": False, "can_be_missing": False,
        },
        "_global_invariants": {
            "current_event_excluded_from_own_history": True,
            "no_future_data_in_any_feature": True,
            "raw_events_immutable": True,
            "fraud_scenario_excluded": True,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def main():
    p = argparse.ArgumentParser(description="Sentinel Phase 1 feature engineering")
    p.add_argument("--input", type=str, default="data/generated/raw_events.csv")
    p.add_argument("--output", type=str, default="data/generated/features.csv")
    p.add_argument("--velocity-window-minutes", type=int, default=DEFAULT_VELOCITY_WINDOW_MIN)
    p.add_argument("--metadata", type=str, default="data/generated/feature_metadata.json")
    args = p.parse_args()

    print("=" * 70)
    print("Sentinel — Phase 1: Feature Engineering")
    print("=" * 70)
    print(f"Input:                  {args.input}")
    print(f"Output:                 {args.output}")
    print(f"Velocity window (min):  {args.velocity_window_minutes}")
    print()

    rows = load_raw(Path(args.input))
    print(f"Loaded {len(rows)} raw events.")

    feature_rows, summary = engineer(rows, args.velocity_window_minutes)

    write_features(feature_rows, Path(args.output))
    write_metadata(Path(args.metadata), args.velocity_window_minutes)

    print()
    print("FEATURE VALIDATION REPORT")
    print("-" * 70)
    print(f"Total rows:                     {summary['total_rows']}")
    print(f"Feature columns (derived):      {summary['feature_columns']}")
    print(f"First-transaction count:        {summary['first_transaction_count']}")
    print(f"Users-with-history count:       {summary['users_with_history_count']}")
    print()
    print("Missing values (null count):")
    for k, v in summary["missing_values"].items():
        print(f"  {k:<40} {v}")
    print()
    print("Velocity statistics")
    sw = summary["velocity_stats"]["short_window"]
    ow = summary["velocity_stats"]["1h"]
    print(f"  {sw['field']}:  min={sw['min']}  max={sw['max']}  mean={sw['mean']:.3f}  nonzero={sw['nonzero_count']}")
    print(f"  transaction_velocity_1h: min={ow['min']} max={ow['max']} mean={ow['mean']:.3f} nonzero={ow['nonzero_count']}")
    print()
    print("Device-sharing statistics")
    ds = summary["device_sharing_stats"]
    print(f"  device_user_count: min={ds['min']} max={ds['max']} mean={ds['mean']:.3f} shared={ds['shared_count']}")
    print()
    print("IP-sharing statistics")
    ips = summary["ip_sharing_stats"]
    print(f"  ip_user_count:     min={ips['min']} max={ips['max']} mean={ips['mean']:.3f} shared={ips['shared_count']}")
    print()
    print("Geographic anomaly statistics")
    gs = summary["geographic_stats"]
    print(f"  with previous location:        {gs['with_previous_location']}")
    print(f"  distance mean (km):            {gs['distance_mean_km']:.2f}")
    print(f"  distance max (km):             {gs['distance_max_km']:.2f}")
    print(f"  velocity mean (km/h):          {gs['velocity_mean_kmh']:.2f}")
    print(f"  velocity max (km/h):           {gs['velocity_max_kmh']:.2f}")
    print()
    print("Representative examples")
    for r in feature_rows[:3]:
        print(f"  txn={r['transaction_id'][:8]}... user={r['user_id'][:8]}... "
              f"is_first={r['is_first_transaction']} "
              f"hist_count={r['historical_transaction_count']} "
              f"vel_5m={r.get(f'transaction_velocity_{args.velocity_window_minutes}m')} "
              f"is_fraud={r['is_fraud']}")
    print()
    print(f"Wrote features:  {args.output}")
    print(f"Wrote metadata:  {args.metadata}")
    print("=" * 70)


if __name__ == "__main__":
    main()
