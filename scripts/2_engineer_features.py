#!/usr/bin/env python3
"""
Sentinel - Phase 1: Temporal Feature Engineering.

Builds leakage-safe, point-in-time features from raw transaction events.

IMPORTANT INVARIANT
-------------------
For a transaction occurring at time T, every historical feature must use
ONLY events strictly before T.

The current transaction is NEVER added to historical state until after all
features for that transaction have been calculated.

The input row order is preserved exactly. The raw event generator is
responsible for producing chronologically ordered data.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple


# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

DEFAULT_VELOCITY_WINDOW_MINUTES = 5

ROOT = Path(__file__).resolve().parents[1]


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def parse_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and normalize it to UTC."""
    ts = datetime.fromisoformat(value)

    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    return ts.astimezone(timezone.utc)


def safe_float(value: str) -> Optional[float]:
    """Convert a CSV value to float, preserving empty values as None."""
    if value is None or value == "":
        return None

    return float(value)


def safe_int(value: str) -> Optional[int]:
    """Convert a CSV value to int, preserving empty values as None."""
    if value is None or value == "":
        return None

    return int(value)


def haversine_km(
    lat1: Optional[float],
    lon1: Optional[float],
    lat2: Optional[float],
    lon2: Optional[float],
) -> Optional[float]:
    """
    Calculate great-circle distance between two coordinates in kilometers.

    Returns None when either location is unavailable.
    """
    if None in (lat1, lon1, lat2, lon2):
        return None

    radius_km = 6371.0088

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radius_km * c


def write_csv(
    rows: List[Dict],
    path: Path,
    fieldnames: List[str],
) -> None:
    """Write engineered rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(rows)


# ----------------------------------------------------------------------------
# Feature engineering
# ----------------------------------------------------------------------------

def engineer(
    rows: List[Dict],
    velocity_window_minutes: int = DEFAULT_VELOCITY_WINDOW_MINUTES,
) -> List[Dict]:
    """
    Engineer point-in-time temporal features.

    CRITICAL:
    - rows are processed in their existing order
    - rows are NEVER sorted here
    - features are calculated BEFORE current-event state mutation
    - all historical features use only strictly prior events
    """

    # ------------------------------------------------------------------------
    # Historical state
    # ------------------------------------------------------------------------

    # Per-user historical transactions:
    # timestamp, amount, transaction_id
    user_history: Dict[
        str,
        Deque[Tuple[datetime, float, str]]
    ] = defaultdict(deque)

    # Historical transaction count per user.
    user_total_count: Dict[str, int] = defaultdict(int)

    # Historical amount sum per user.
    user_amount_sum: Dict[str, float] = defaultdict(float)

    # Historical device -> users relationship.
    device_users: Dict[str, set] = defaultdict(set)

    # Historical IP -> users relationship.
    ip_users: Dict[str, set] = defaultdict(set)

    # Previous transaction timestamp per user.
    user_last_timestamp: Dict[str, datetime] = {}

    # Previous transaction location per user.
    user_last_location: Dict[str, Tuple[float, float]] = {}

    user_last_device: Dict[str, str] = {}
    user_last_ip: Dict[str, str] = {}

    user_devices_seen: Dict[str, set] = defaultdict(set)
    user_ips_seen: Dict[str, set] = defaultdict(set)

    # Historical failed transaction timestamps per user.
    user_failed_history: Dict[str, Deque[datetime]] = defaultdict(deque)

    # ------------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------------

    engineered_rows: List[Dict] = []

    # ------------------------------------------------------------------------
    # Process input EXACTLY in existing order.
    #
    # DO NOT SORT HERE.
    #
    # The raw generator guarantees chronological order.
    # ------------------------------------------------------------------------

    for row in rows:
        user = row["user_id"]
        device = row["device_fingerprint"]
        ip = row["ip_address"]

        timestamp = parse_timestamp(row["timestamp"])

        amount = safe_float(row["transaction_amount"])
        if amount is None:
            amount = 0.0

        latitude = safe_float(row.get("latitude"))
        longitude = safe_float(row.get("longitude"))

        payment_attempt_number = safe_int(
            row.get("payment_attempt_number")
        )

        transaction_status = row.get("transaction_status", "")

        # --------------------------------------------------------------------
        # EVERYTHING BELOW USES STATE FROM BEFORE CURRENT EVENT.
        # --------------------------------------------------------------------

        historical_count = user_total_count[user]

        # --------------------------------------------------------------------
        # Historical amount
        # --------------------------------------------------------------------

        has_historical_amount = historical_count > 0

        if has_historical_amount:
            historical_avg_amount = (
                user_amount_sum[user] / historical_count
            )
        else:
            historical_avg_amount = None

        is_first_transaction = historical_count == 0

        # --------------------------------------------------------------------
        # Previous transaction
        # --------------------------------------------------------------------

        previous_timestamp = user_last_timestamp.get(user)

        if previous_timestamp is None:
            time_since_previous_transaction = None
        else:
            delta = timestamp - previous_timestamp
            time_since_previous_transaction = delta.total_seconds()

        # --------------------------------------------------------------------
        # Previous location
        # --------------------------------------------------------------------

        previous_location = user_last_location.get(user)

        has_previous_location = previous_location is not None

        geographic_distance_from_previous = haversine_km(
            latitude,
            longitude,
            previous_location[0] if previous_location else None,
            previous_location[1] if previous_location else None,
        )

        # --------------------------------------------------------------------
        # Historical velocity
        # --------------------------------------------------------------------

        history = user_history[user]

        max_window = max(
            velocity_window_minutes,
            60,
        )

        cutoff = timestamp - timedelta(minutes=max_window)

        while history and history[0][0] < cutoff:
            history.popleft()

        velocity_5m = 0
        velocity_1h = 0

        five_min_cutoff = timestamp - timedelta(minutes=5)
        one_hour_cutoff = timestamp - timedelta(hours=1)

        for historical_timestamp, _, _ in history:
            # Explicitly require strict temporal ordering.
            if historical_timestamp < timestamp:

                if historical_timestamp >= five_min_cutoff:
                    velocity_5m += 1

                if historical_timestamp >= one_hour_cutoff:
                    velocity_1h += 1

        # --------------------------------------------------------------------
        # Historical device/IP relationship counts
        #
        # Current user is NOT added until after these values are calculated.
        # --------------------------------------------------------------------

        device_user_count = len(device_users[device])
        ip_user_count = len(ip_users[ip])

        # Distinct devices previously used by this user.
        unique_devices_seen_before = len(
            user_devices_seen[user]
        )

        unique_ips_seen_before = len(
            user_ips_seen[user]
        )

        # --------------------------------------------------------------------
        # Failed-attempt velocity
        # --------------------------------------------------------------------

        failed_history = user_failed_history[user]

        failed_cutoff = timestamp - timedelta(hours=1)

        while (
            failed_history
            and failed_history[0] < failed_cutoff
        ):
            failed_history.popleft()

        failed_attempt_velocity = sum(
            1
            for failed_timestamp in failed_history
            if failed_timestamp < timestamp
        )

        # --------------------------------------------------------------------
        # Amount anomaly
        # --------------------------------------------------------------------

        if (
            historical_avg_amount is None
            or historical_avg_amount == 0
        ):
            amount_ratio_to_history = None
        else:
            amount_ratio_to_history = (
                amount / historical_avg_amount
            )

        # --------------------------------------------------------------------
        # Geographic velocity
        #
        # Distance divided by elapsed time in hours.
        # This is only calculated when a previous location and previous
        # timestamp exist.
        # --------------------------------------------------------------------

        geographic_velocity = None

        if (
            geographic_distance_from_previous is not None
            and time_since_previous_transaction is not None
            and time_since_previous_transaction > 0
        ):
            geographic_velocity = (
                geographic_distance_from_previous
                / (time_since_previous_transaction / 3600.0)
            )

        # --------------------------------------------------------------------
        # Account age
        # --------------------------------------------------------------------

        account_creation_timestamp = parse_timestamp(
            row["account_creation_timestamp"]
        )

        account_age_seconds = (
            timestamp - account_creation_timestamp
        ).total_seconds()

        # Protect against malformed future account timestamps.
        if account_age_seconds < 0:
            account_age_seconds = 0.0

        # --------------------------------------------------------------------
        # Build engineered row.
        #
        # Start from original row so ALL raw columns remain preserved.
        # --------------------------------------------------------------------

        engineered = dict(row)

        # Existing feature names used by earlier tests.
        engineered["historical_transaction_count"] = historical_count

        engineered["historical_avg_amount"] = (
            historical_avg_amount
        )

        engineered["is_first_transaction"] = (
            "true"
            if is_first_transaction
            else "false"
        )

        # Preserve existing feature for compatibility.
        engineered[
            "time_since_last_transaction_minutes"
        ] = (
            None
            if time_since_previous_transaction is None
            else time_since_previous_transaction / 60.0
        )

        engineered["transaction_velocity_5m"] = velocity_5m
        engineered["transaction_velocity_1h"] = velocity_1h

        engineered["device_user_count"] = device_user_count
        engineered["ip_user_count"] = ip_user_count

        engineered[
            "amount_vs_historical_avg"
        ] = amount_ratio_to_history

        # --------------------------------------------------------------------
        # Canonical model features.
        # These names MUST match selected_features.json exactly.
        # --------------------------------------------------------------------

        engineered[
            "has_historical_amount"
        ] = (
            "true"
            if has_historical_amount
            else "false"
        )

        engineered[
            "has_previous_location"
        ] = (
            "true"
            if has_previous_location
            else "false"
        )

        engineered[
            "amount_ratio_to_history"
        ] = amount_ratio_to_history

        engineered[
            "time_since_previous_transaction"
        ] = time_since_previous_transaction

        engineered[
            "unique_devices_seen_before"
        ] = unique_devices_seen_before

        engineered[
            "unique_ips_seen_before"
        ] = unique_ips_seen_before

        engineered[
            "failed_attempt_velocity"
        ] = failed_attempt_velocity

        engineered[
            "geographic_distance_from_previous"
        ] = geographic_distance_from_previous

        engineered[
            "geographic_velocity"
        ] = geographic_velocity

        engineered[
            "account_age_seconds"
        ] = account_age_seconds

        # --------------------------------------------------------------------
        # NOW mutate historical state.
        #
        # This MUST happen only after every feature has been calculated.
        # --------------------------------------------------------------------

        history.append(
            (
                timestamp,
                amount,
                row["transaction_id"],
            )
        )

        user_total_count[user] += 1
        user_amount_sum[user] += amount
        user_last_timestamp[user] = timestamp

        if latitude is not None and longitude is not None:
            user_last_location[user] = (
                latitude,
                longitude,
            )

        user_last_device[user] = device
        user_last_ip[user] = ip
        user_devices_seen[user].add(device)
        user_ips_seen[user].add(ip)

        device_users[device].add(user)
        ip_users[ip].add(user)

        if transaction_status.lower() == "failed":
            failed_history.append(timestamp)

        engineered_rows.append(engineered)

    return engineered_rows


# ----------------------------------------------------------------------------
# Metadata
# ----------------------------------------------------------------------------

def build_feature_metadata() -> Dict[str, Dict]:
    """
    Metadata describing all raw and engineered features.

    Historical features explicitly document that they use only past state.
    """

    return {
        # --------------------------------------------------------------------
        # Raw columns
        # --------------------------------------------------------------------

        "transaction_id": {
            "description": "Opaque UUID transaction identifier.",
            "dtype": "string",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "timestamp": {
            "description": "ISO-8601 UTC transaction timestamp.",
            "dtype": "datetime",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "user_id": {
            "description": "Opaque user identifier.",
            "dtype": "string",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "merchant_id": {
            "description": "Opaque merchant identifier.",
            "dtype": "string",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "device_fingerprint": {
            "description": "Opaque device fingerprint.",
            "dtype": "string",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "ip_address": {
            "description": "IPv4 address.",
            "dtype": "string",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "payment_method": {
            "description": "Payment method used by the transaction.",
            "dtype": "string",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "transaction_amount": {
            "description": "Transaction amount.",
            "dtype": "float",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "currency": {
            "description": "Transaction currency.",
            "dtype": "string",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "latitude": {
            "description": "Transaction latitude.",
            "dtype": "float",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "longitude": {
            "description": "Transaction longitude.",
            "dtype": "float",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "transaction_status": {
            "description": "Transaction status.",
            "dtype": "string",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "account_creation_timestamp": {
            "description": "Account creation timestamp.",
            "dtype": "datetime",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "payment_attempt_number": {
            "description": "Payment attempt number.",
            "dtype": "integer",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "transaction_type": {
            "description": "Transaction type.",
            "dtype": "string",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "is_fraud": {
            "description": "Ground-truth fraud label.",
            "dtype": "boolean",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        "fraud_scenario": {
            "description": (
                "Validation-only fraud scenario metadata; "
                "must not be used as a model feature."
            ),
            "dtype": "string",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        # --------------------------------------------------------------------
        # Historical/model features
        # --------------------------------------------------------------------

        "historical_transaction_count": {
            "description": (
                "Number of transactions by this user strictly before "
                "the current transaction."
            ),
            "dtype": "integer",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": False,
        },

        "historical_avg_amount": {
            "description": (
                "Average amount of this user's transactions strictly "
                "before the current transaction."
            ),
            "dtype": "float",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": True,
        },

        "is_first_transaction": {
            "description": (
                "Whether this is the user's first transaction."
            ),
            "dtype": "boolean",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": False,
        },

        "has_historical_amount": {
            "description": (
                "Whether the user has at least one historical "
                "transaction before the current event."
            ),
            "dtype": "boolean",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": False,
        },

        "has_previous_location": {
            "description": (
                "Whether the user has a previous transaction location."
            ),
            "dtype": "boolean",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": False,
        },

        "amount_ratio_to_history": {
            "description": (
                "Current transaction amount divided by the user's "
                "historical average amount."
            ),
            "dtype": "float",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": True,
        },

        "transaction_velocity_5m": {
            "description": (
                "Number of prior transactions by this user within "
                "the previous five minutes."
            ),
            "dtype": "integer",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": False,
        },

        "transaction_velocity_1h": {
            "description": (
                "Number of prior transactions by this user within "
                "the previous one hour."
            ),
            "dtype": "integer",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": False,
        },

        "time_since_previous_transaction": {
            "description": (
                "Seconds since the user's immediately preceding "
                "transaction."
            ),
            "dtype": "float",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": True,
        },

        "unique_devices_seen_before": {
            "description": (
                "Number of distinct devices previously observed for "
                "this user."
            ),
            "dtype": "integer",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": False,
        },

        "unique_ips_seen_before": {
            "description": (
                "Number of distinct IP addresses previously observed "
                "for this user."
            ),
            "dtype": "integer",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": False,
        },

        "device_user_count": {
            "description": (
                "Number of distinct users previously observed on "
                "the current device."
            ),
            "dtype": "integer",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": False,
        },

        "ip_user_count": {
            "description": (
                "Number of distinct users previously observed on "
                "the current IP address."
            ),
            "dtype": "integer",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": False,
        },

        "failed_attempt_velocity": {
            "description": (
                "Number of prior failed transactions by this user "
                "within the previous hour."
            ),
            "dtype": "integer",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": False,
        },

        "geographic_distance_from_previous": {
            "description": (
                "Great-circle distance in kilometers from the user's "
                "previous transaction location."
            ),
            "dtype": "float",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": True,
        },

        "geographic_velocity": {
            "description": (
                "Distance from previous location divided by elapsed "
                "time, in kilometers per hour."
            ),
            "dtype": "float",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": True,
        },

        "account_age_seconds": {
            "description": (
                "Age of the user's account at transaction time."
            ),
            "dtype": "float",
            "uses_future_data": False,
            "historical": False,
            "can_be_missing": False,
        },

        # --------------------------------------------------------------------
        # Compatibility aliases
        # --------------------------------------------------------------------

        "time_since_last_transaction_minutes": {
            "description": (
                "Compatibility alias for time since previous "
                "transaction, expressed in minutes."
            ),
            "dtype": "float",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": True,
        },

        "amount_vs_historical_avg": {
            "description": (
                "Compatibility alias for amount ratio to historical "
                "average."
            ),
            "dtype": "float",
            "uses_future_data": False,
            "historical": True,
            "can_be_missing": True,
        },
    }


def write_metadata(
    path: Path,
    velocity_window_minutes: int,
) -> None:
    """Write feature-engineering metadata."""
    metadata = build_feature_metadata()

    payload = {
        "velocity_window_minutes": velocity_window_minutes,
        "features": metadata,
    }

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            payload,
            f,
            indent=2,
        )


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sentinel Phase 1 temporal feature engineering"
    )

    parser.add_argument(
        "--input",
        type=str,
        default="data/generated/raw_events.csv",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="data/generated/features.csv",
    )

    parser.add_argument(
        "--metadata",
        type=str,
        default="data/generated/feature_metadata.json",
    )

    parser.add_argument(
        "--velocity-window-minutes",
        type=int,
        default=DEFAULT_VELOCITY_WINDOW_MINUTES,
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    metadata_path = Path(args.metadata)

    # ------------------------------------------------------------------------
    # Read raw CSV.
    #
    # IMPORTANT: Do not sort.
    # ------------------------------------------------------------------------

    with input_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError(
            "Input raw event dataset is empty."
        )

    # ------------------------------------------------------------------------
    # Verify chronological order.
    # ------------------------------------------------------------------------

    timestamps = [
        parse_timestamp(row["timestamp"])
        for row in rows
    ]

    if timestamps != sorted(timestamps):
        raise ValueError(
            "Input raw events are not chronologically ordered. "
            "Run the raw event generator first."
        )

    # ------------------------------------------------------------------------
    # Engineer features.
    # ------------------------------------------------------------------------

    engineered_rows = engineer(
        rows,
        velocity_window_minutes=args.velocity_window_minutes,
    )

    # ------------------------------------------------------------------------
    # Preserve original CSV columns and append engineered columns.
    # ------------------------------------------------------------------------

    original_fields = list(rows[0].keys())

    engineered_fields = [
        "historical_transaction_count",
        "historical_avg_amount",
        "is_first_transaction",
        "time_since_last_transaction_minutes",
        "transaction_velocity_5m",
        "transaction_velocity_1h",
        "device_user_count",
        "ip_user_count",
        "amount_vs_historical_avg",

        # Canonical model features.
        "has_historical_amount",
        "has_previous_location",
        "amount_ratio_to_history",
        "time_since_previous_transaction",
        "unique_devices_seen_before",
        "unique_ips_seen_before",
        "failed_attempt_velocity",
        "geographic_distance_from_previous",
        "geographic_velocity",
        "account_age_seconds",
    ]

    fieldnames = original_fields + engineered_fields

    # ------------------------------------------------------------------------
    # Write output.
    # ------------------------------------------------------------------------

    write_csv(
        engineered_rows,
        output_path,
        fieldnames,
    )

    write_metadata(
        metadata_path,
        args.velocity_window_minutes,
    )

    # ------------------------------------------------------------------------
    # Validate the model feature contract immediately.
    # ------------------------------------------------------------------------

    selected_features_path = ROOT / "artifacts" / "selected_features.json"

    if selected_features_path.exists():
        with selected_features_path.open(
            "r",
            encoding="utf-8",
        ) as f:
            selected_features = json.load(f)

        missing_features = [
            feature
            for feature in selected_features
            if feature not in fieldnames
        ]

        if missing_features:
            raise RuntimeError(
                "Generated features.csv is missing model features: "
                + ", ".join(missing_features)
            )

    # ------------------------------------------------------------------------
    # Report.
    # ------------------------------------------------------------------------

    print("=" * 70)
    print("Sentinel - Phase 1: Temporal Feature Engineering")
    print("=" * 70)
    print(f"Input:                       {input_path}")
    print(f"Output:                      {output_path}")
    print(f"Metadata:                    {metadata_path}")
    print(f"Rows:                        {len(engineered_rows)}")
    print(
        f"Velocity window:             "
        f"{args.velocity_window_minutes} minutes"
    )
    print()

    print("Temporal safety:")
    print("  - Input row order preserved: YES")
    print("  - Input verified chronological: YES")
    print("  - Current event excluded: YES")
    print("  - Future data used: NO")
    print("  - State updated after features: YES")

    print()

    print("Feature contract:")
    print("  - selected_features.json compatibility: YES")
    print(f"  - Model features available: {len(selected_features) if selected_features_path.exists() else 'N/A'}")

    print("=" * 70)


if __name__ == "__main__":
    main()