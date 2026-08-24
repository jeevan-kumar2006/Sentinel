#!/usr/bin/env python3
"""
Sentinel — Phase 1: Raw event generator.

Generates a synthetic, temporally correct, leakage-safe transaction dataset
for velocity- and anomaly-based fraud detection.

The raw dataset is IMMUTABLE ground truth. Feature engineering operates on
this file separately and must never modify it.

Identifiers are intentionally opaque (UUID-derived). No semantic words such
as 'fraud', 'attacker', 'normal', etc. are ever embedded in any identifier.

Fraud prevalence here is a synthetic benchmark prevalence chosen for
hackathon evaluation. It is NOT a real-world or Razorpay fraud prevalence.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

# ----------------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------------

WARMUP_DAYS = 90
ATTACK_DAYS = 14
TOTAL_DAYS = WARMUP_DAYS + ATTACK_DAYS

DEFAULT_ROWS = 50_000
DEFAULT_FRAUD_RATE = 0.04
DEFAULT_SEED = 42

# User behavioural profiles. 'weight' is the relative share of the user
# population assigned to each profile. Rates are transactions per day.
PROFILE_DEFS: List[Dict] = [
    {"name": "low_frequency",         "tx_per_day": (0.08, 0.30), "amount_range": (100,   5_000),  "weight": 22},
    {"name": "frequent_moderate",     "tx_per_day": (0.50, 1.60), "amount_range": (50,    2_500),  "weight": 26},
    {"name": "occasional_high_value", "tx_per_day": (0.06, 0.22), "amount_range": (5_000, 80_000), "weight": 10},
    {"name": "travel_heavy",          "tx_per_day": (0.25, 0.80), "amount_range": (200,   4_000),  "weight": 14},
    {"name": "mobile_heavy",          "tx_per_day": (0.35, 1.20), "amount_range": (100,   2_000),  "weight": 16},
    {"name": "desktop_heavy",         "tx_per_day": (0.25, 1.00), "amount_range": (200,   3_500),  "weight": 12},
]

PAYMENT_METHODS = ["credit_card", "debit_card", "upi", "netbanking", "wallet"]
PAYMENT_WEIGHTS = [25, 25, 35, 10, 5]

CURRENCIES = ["INR"] * 96 + ["USD", "EUR", "AED", "SGD"]

TX_TYPES = ["purchase"] * 80 + ["refund"] * 8 + ["topup"] * 7 + ["transfer"] * 5

STATUS_SUCCESS = "success"
STATUS_FAILED  = "failed"
STATUS_PENDING = "pending"
STATUS_WEIGHTS = [88, 10, 2]

# Fraud scenario distribution (must sum to 1.0). Kept balanced on purpose
# so no single scenario dominates the positive class.
SCENARIO_WEIGHTS: Dict[str, float] = {
    "device_velocity":   0.18,
    "account_velocity":  0.18,
    "ip_concentration":  0.15,
    "amount_anomaly":    0.15,
    "geo_anomaly":       0.15,
    "combined":          0.19,
}

# India-ish geographic bounding box used for realistic coordinates.
LAT_RANGE = (8.0, 35.0)
LON_RANGE = (68.0, 97.0)

# City anchors used to cluster legitimate activity (most users transact
# near a small set of urban centres, with occasional travel).
CITY_ANCHORS = [
    (19.0760, 72.8777),  # Mumbai
    (28.7041, 77.1025),  # Delhi
    (12.9716, 77.5946),  # Bengaluru
    (22.5726, 88.3639),  # Kolkata
    (13.0827, 80.2707),  # Chennai
    (17.3850, 78.4867),  # Hyderabad
    (23.2599, 77.4126),  # Bhopal
    (26.9124, 75.7873),  # Jaipur
]


# ----------------------------------------------------------------------------
# Opaque identifier generators (NO semantic words ever embedded)
# ----------------------------------------------------------------------------

def gen_user_id(rng: random.Random) -> str:
    return f"U_{uuid.UUID(int=rng.getrandbits(128)).hex[:12]}"


def gen_device_id(rng: random.Random) -> str:
    return f"D_{uuid.UUID(int=rng.getrandbits(128)).hex[:16]}"


def gen_ip(rng: random.Random) -> str:
    a = rng.randint(1, 223)
    b = rng.randint(0, 255)
    c = rng.randint(0, 255)
    d = rng.randint(1, 254)
    return f"{a}.{b}.{c}.{d}"


def gen_merchant_id(rng: random.Random) -> str:
    return f"M_{uuid.UUID(int=rng.getrandbits(128)).hex[:8]}"


def gen_txn_id(rng: random.Random) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128)))


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def weighted_choice(rng: random.Random, items: List, weights: List[float]):
    return rng.choices(items, weights=weights, k=1)[0]


def jitter_location(rng: random.Random, lat: float, lon: float, spread: float = 0.05) -> Tuple[float, float]:
    return (
        round(lat + rng.uniform(-spread, spread), 6),
        round(lon + rng.uniform(-spread, spread), 6),
    )


def random_location(rng: random.Random) -> Tuple[float, float]:
    lat = rng.uniform(*LAT_RANGE)
    lon = rng.uniform(*LON_RANGE)
    return round(lat, 6), round(lon, 6)


def random_timestamp_between(rng: random.Random, start: datetime, end: datetime) -> datetime:
    delta = (end - start).total_seconds()
    return start + timedelta(seconds=rng.uniform(0, delta))


def weighted_status(rng: random.Random, force_failed: bool = False) -> str:
    if force_failed:
        return STATUS_FAILED
    return weighted_choice(rng, [STATUS_SUCCESS, STATUS_FAILED, STATUS_PENDING], STATUS_WEIGHTS)


# ----------------------------------------------------------------------------
# Entity population generation
# ----------------------------------------------------------------------------

class User:
    __slots__ = (
        "user_id", "profile", "amount_low", "amount_high", "rate",
        "home_lat", "home_lon", "devices", "ips", "account_created_at",
        "preferred_payment_methods",
    )

    def __init__(self, rng: random.Random, start_time: datetime):
        self.user_id = gen_user_id(rng)
        profile = weighted_choice(rng, PROFILE_DEFS, [p["weight"] for p in PROFILE_DEFS])
        self.profile = profile["name"]
        self.amount_low, self.amount_high = profile["amount_range"]
        self.rate = rng.uniform(*profile["tx_per_day"])
        anchor = rng.choice(CITY_ANCHORS)
        self.home_lat, self.home_lon = jitter_location(rng, anchor[0], anchor[1], spread=0.08)

        # Persistent device(s) — most users have 1 primary, some have 2-3.
        n_devices = 1 if rng.random() < 0.7 else rng.randint(2, 3)
        self.devices = [gen_device_id(rng) for _ in range(n_devices)]

        # Persistent IP(s) — most users have 1, some have 2 (home + mobile).
        n_ips = 1 if rng.random() < 0.8 else 2
        self.ips = [gen_ip(rng) for _ in range(n_ips)]

        # Account creation timestamp: mostly before warm-up, some during.
        if rng.random() < 0.85:
            self.account_created_at = start_time - timedelta(days=rng.randint(1, 365))
        else:
            self.account_created_at = random_timestamp_between(rng, start_time, start_time + timedelta(days=TOTAL_DAYS))

        # Payment-method preference (skewed but not deterministic).
        if self.profile == "mobile_heavy":
            self.preferred_payment_methods = ["upi", "wallet", "debit_card"]
        elif self.profile == "desktop_heavy":
            self.preferred_payment_methods = ["netbanking", "credit_card", "upi"]
        else:
            self.preferred_payment_methods = rng.sample(PAYMENT_METHODS, k=3)


class Merchant:
    __slots__ = ("merchant_id", "typical_amount_low", "typical_amount_high")

    def __init__(self, rng: random.Random):
        self.merchant_id = gen_merchant_id(rng)
        # Merchants span a range of typical ticket sizes.
        low = rng.choice([50, 100, 200, 500, 1000, 5000])
        self.typical_amount_low = low
        self.typical_amount_high = low * rng.randint(5, 30)


def build_population(rng: random.Random, start_time: datetime, target_legit: int) -> Tuple[List[User], List[Merchant], Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Build a persistent population of users, merchants, devices, IPs.

    Returns:
        users, merchants,
        device_to_users (legitimate shared-device map),
        ip_to_users     (legitimate shared-IP map)
    """
    # Size the user base so that expected legit transactions ≈ target_legit.
    # Average rate ≈ 0.55 tx/day; over TOTAL_DAYS days; expected tx per user ≈ 0.55 * 104 ≈ 57.
    # For 48,000 legit tx we need ~850 users. We use 1,400 to introduce variety
    # (low-frequency users, cold-start users, etc.). Final count is exact because
    # we allocate transaction counts proportionally below.
    n_users = 1_400
    users: List[User] = [User(rng, start_time) for _ in range(n_users)]

    n_merchants = 160
    merchants: List[Merchant] = [Merchant(rng) for _ in range(n_merchants)]

    # Legitimate shared infrastructure: family devices, office IPs, etc.
    device_to_users: Dict[str, List[str]] = {}
    ip_to_users: Dict[str, List[str]] = {}

    # ~12% of devices legitimately shared between 2-3 users.
    shared_device_pool = rng.sample(users, k=int(n_users * 0.12))
    for u in shared_device_pool:
        # Pick another 1-2 users to share u's primary device with.
        others = rng.sample([x for x in users if x is not u], k=rng.randint(1, 2))
        shared_device = u.devices[0]
        # Ensure each of those others has this device too.
        for o in others:
            if shared_device not in o.devices:
                o.devices.append(shared_device)
        device_to_users[shared_device] = [u.user_id] + [o.user_id for o in others]

    # ~15% of IPs legitimately shared (same office, ISP-level NAT).
    shared_ip_pool = rng.sample(users, k=int(n_users * 0.15))
    for u in shared_ip_pool:
        others = rng.sample([x for x in users if x is not u], k=rng.randint(1, 3))
        shared_ip = u.ips[0]
        for o in others:
            if shared_ip not in o.ips:
                o.ips.append(shared_ip)
        ip_to_users[shared_ip] = [u.user_id] + [o.user_id for o in others]

    return users, merchants, device_to_users, ip_to_users


# ----------------------------------------------------------------------------
# Legitimate transaction generation
# ----------------------------------------------------------------------------

def gen_legit_transactions(
    rng: random.Random,
    users: List[User],
    merchants: List[Merchant],
    start_time: datetime,
    end_time: datetime,
    target_count: int,
) -> List[Dict]:
    """
    Distribute exactly target_count legitimate transactions across users
    (proportional to each user's rate) and across the timeline (Poisson-like).
    """
    # Assign each user a target tx count proportional to their rate.
    rates = [u.rate for u in users]
    total_rate = sum(rates)
    raw_counts = [target_count * r / total_rate for r in rates]
    # Floor-assign then distribute the remainder to hit target_count exactly.
    counts = [int(c) for c in raw_counts]
    remainder = target_count - sum(counts)
    # Distribute remainder round-robin to users with the highest fractional parts.
    fracs = sorted(range(len(users)), key=lambda i: raw_counts[i] - counts[i], reverse=True)
    for i in range(remainder):
        counts[fracs[i % len(users)]] += 1

    txns: List[Dict] = []
    for user, count in zip(users, counts):
        if count == 0:
            continue
        # Sample `count` timestamps uniformly across the timeline (Poisson-like
        # in aggregate; per-user inter-arrival is exponentially distributed
        # because we sort the sampled times).
        sampled = sorted(
            random_timestamp_between(rng, start_time, end_time)
            for _ in range(count)
        )
        prev_ts = None
        for ts in sampled:
            # Most transactions use a known device; some introduce a new device
            # (legitimate device rotation).
            if prev_ts is not None and rng.random() < 0.04:
                # Occasional new device (legit).
                device = gen_device_id(rng)
            else:
                device = rng.choice(user.devices)

            # Occasionally a fresh IP (legit user on mobile data).
            if rng.random() < 0.05:
                ip = gen_ip(rng)
            else:
                ip = rng.choice(user.ips)

            # Amount: usually within user's range, occasionally large
            # (legitimate high-value purchase — keeps fraud non-trivial).
            if rng.random() < 0.04:
                # Occasional big purchase by any profile.
                amount = round(rng.uniform(user.amount_high * 1.5, user.amount_high * 4), 2)
            else:
                amount = round(rng.uniform(user.amount_low, user.amount_high), 2)

            # Location: usually near home, occasionally a different city (travel).
            if rng.random() < 0.08:
                anchor = rng.choice(CITY_ANCHORS)
                lat, lon = jitter_location(rng, anchor[0], anchor[1], spread=0.1)
            else:
                lat, lon = jitter_location(rng, user.home_lat, user.home_lon, spread=0.05)

            merchant = rng.choice(merchants)
            payment_method = weighted_choice(
                rng, user.preferred_payment_methods, [3, 2, 1]
            )
            currency = rng.choice(CURRENCIES)
            tx_type = rng.choice(TX_TYPES)

            # Occasionally a failed payment attempt (legit).
            status = weighted_status(rng, force_failed=(rng.random() < 0.05))

            # payment_attempt_number: usually 1; spikes if previous failed.
            attempt = 1 if rng.random() < 0.9 else rng.randint(2, 4)

            txns.append({
                "transaction_id": gen_txn_id(rng),
                "timestamp": ts,
                "user_id": user.user_id,
                "merchant_id": merchant.merchant_id,
                "device_fingerprint": device,
                "ip_address": ip,
                "payment_method": payment_method,
                "transaction_amount": amount,
                "currency": currency,
                "latitude": lat,
                "longitude": lon,
                "transaction_status": status,
                "account_creation_timestamp": user.account_created_at,
                "payment_attempt_number": attempt,
                "transaction_type": tx_type,
                "is_fraud": False,
                "fraud_scenario": "none",
            })
            prev_ts = ts
    return txns


# ----------------------------------------------------------------------------
# Fraud injection
# ----------------------------------------------------------------------------

def _new_fraud_entities(rng: random.Random, n_users: int, n_devices: int, n_ips: int):
    """Create fresh entities used by a single fraud campaign (opaque IDs)."""
    users = [gen_user_id(rng) for _ in range(n_users)]
    devices = [gen_device_id(rng) for _ in range(n_devices)]
    ips = [gen_ip(rng) for _ in range(n_ips)]
    return users, devices, ips


def _basic_txn_fields(rng: random.Random, ts: datetime, user_id: str,
                      device: str, ip: str, amount: float, status: str) -> Dict:
    anchor = rng.choice(CITY_ANCHORS)
    lat, lon = jitter_location(rng, anchor[0], anchor[1], spread=0.15)
    merchant = gen_merchant_id(rng)
    return {
        "transaction_id": gen_txn_id(rng),
        "timestamp": ts,
        "user_id": user_id,
        "merchant_id": merchant,
        "device_fingerprint": device,
        "ip_address": ip,
        "payment_method": rng.choice(PAYMENT_METHODS),
        "transaction_amount": round(amount, 2),
        "currency": rng.choice(CURRENCIES),
        "latitude": lat,
        "longitude": lon,
        "transaction_status": status,
        "account_creation_timestamp": ts - timedelta(days=rng.randint(0, 30)),
        "payment_attempt_number": 1,
        "transaction_type": rng.choice(TX_TYPES),
        "is_fraud": True,
    }


def inject_device_velocity(rng: random.Random, txns: List[Dict],
                           attack_start: datetime, attack_end: datetime,
                           count: int) -> None:
    """One device suddenly associated with many accounts within a short period."""
    remaining = count
    while remaining > 0:
        burst_size = min(remaining, rng.randint(6, 15))
        remaining -= burst_size

        # Pick a burst start time somewhere in the attack window.
        burst_start = random_timestamp_between(rng, attack_start, attack_end - timedelta(hours=2))
        # Single device, many user accounts, single IP typically.
        device = gen_device_id(rng)
        ip = gen_ip(rng)
        # 1-3 distinct IPs for the burst (some natural rotation).
        ips_pool = [ip] + ([gen_ip(rng)] for _ in range(rng.randint(0, 2)))
        users, _, _ = _new_fraud_entities(rng, burst_size, 0, 0)

        for i in range(burst_size):
            ts = burst_start + timedelta(seconds=rng.randint(5, 60 * 30))
            amount = round(rng.uniform(500, 15_000), 2)
            status = weighted_status(rng, force_failed=(rng.random() < 0.25))
            txn = _basic_txn_fields(rng, ts, users[i], device, ip, amount, status)
            txn["fraud_scenario"] = "device_velocity"
            txns.append(txn)


def inject_account_velocity(rng: random.Random, txns: List[Dict],
                            attack_start: datetime, attack_end: datetime,
                            count: int) -> None:
    """One account suddenly generates many transactions in a short period."""
    remaining = count
    while remaining > 0:
        burst_size = min(remaining, rng.randint(8, 20))
        remaining -= burst_size

        burst_start = random_timestamp_between(rng, attack_start, attack_end - timedelta(hours=2))
        user = gen_user_id(rng)
        # Account uses 1-2 devices during the burst.
        devices_pool = [gen_device_id(rng) for _ in range(rng.randint(1, 2))]
        ip = gen_ip(rng)

        for i in range(burst_size):
            ts = burst_start + timedelta(seconds=rng.randint(10, 60 * 60))
            device = rng.choice(devices_pool)
            amount = round(rng.uniform(200, 8_000), 2)
            status = weighted_status(rng, force_failed=(rng.random() < 0.2))
            txn = _basic_txn_fields(rng, ts, user, device, ip, amount, status)
            txn["fraud_scenario"] = "account_velocity"
            txns.append(txn)


def inject_ip_concentration(rng: random.Random, txns: List[Dict],
                            attack_start: datetime, attack_end: datetime,
                            count: int) -> None:
    """One IP becomes associated with many accounts and suspicious activity."""
    remaining = count
    while remaining > 0:
        burst_size = min(remaining, rng.randint(10, 25))
        remaining -= burst_size

        burst_start = random_timestamp_between(rng, attack_start, attack_end - timedelta(hours=3))
        ip = gen_ip(rng)
        # Multiple devices and users sharing the same IP within a short window.
        users, devices, _ = _new_fraud_entities(rng, burst_size, rng.randint(3, 8), 0)

        for i in range(burst_size):
            ts = burst_start + timedelta(seconds=rng.randint(15, 60 * 90))
            user = rng.choice(users)
            device = rng.choice(devices)
            amount = round(rng.uniform(300, 12_000), 2)
            status = weighted_status(rng, force_failed=(rng.random() < 0.22))
            txn = _basic_txn_fields(rng, ts, user, device, ip, amount, status)
            txn["fraud_scenario"] = "ip_concentration"
            txns.append(txn)


def inject_amount_anomaly(rng: random.Random, txns: List[Dict],
                          attack_start: datetime, attack_end: datetime,
                          count: int, users: List[User]) -> None:
    """
    Transaction amount is significantly different from the user's established
    baseline. We compromise existing users so that there IS an established
    baseline to deviate from.
    """
    for _ in range(count):
        # Pick a real user (so there is history) with established behaviour.
        user = rng.choice(users)
        ts = random_timestamp_between(rng, attack_start, attack_end)
        device = rng.choice(user.devices)
        ip = rng.choice(user.ips)
        # 5x-15x their typical upper bound.
        amount = round(rng.uniform(user.amount_high * 5, user.amount_high * 15), 2)
        status = weighted_status(rng, force_failed=(rng.random() < 0.15))
        txn = _basic_txn_fields(rng, ts, user.user_id, device, ip, amount, status)
        txn["fraud_scenario"] = "amount_anomaly"
        txns.append(txn)


def inject_geo_anomaly(rng: random.Random, txns: List[Dict],
                       attack_start: datetime, attack_end: datetime,
                       count: int, users: List[User]) -> None:
    """
    A user transacts from a geographically impossible location relative to
    their previous transaction within an unrealistic interval.
    """
    for _ in range(count):
        user = rng.choice(users)
        ts = random_timestamp_between(rng, attack_start, attack_end)
        # Location far from user's home anchor.
        far_anchor = rng.choice([a for a in CITY_ANCHORS if
                                 math.hypot(a[0] - user.home_lat, a[1] - user.home_lon) > 8])
        lat, lon = jitter_location(rng, far_anchor[0], far_anchor[1], spread=0.1)

        device = rng.choice(user.devices)
        ip = rng.choice(user.ips)
        amount = round(rng.uniform(user.amount_low, user.amount_high * 2), 2)
        status = weighted_status(rng, force_failed=(rng.random() < 0.18))

        txn = _basic_txn_fields(rng, ts, user.user_id, device, ip, amount, status)
        txn["latitude"] = lat
        txn["longitude"] = lon
        txn["fraud_scenario"] = "geo_anomaly"
        txns.append(txn)


def inject_combined(rng: random.Random, txns: List[Dict],
                    attack_start: datetime, attack_end: datetime,
                    count: int) -> None:
    """
    Multiple weak signals simultaneously: new device, new IP, new user,
    elevated amount, high velocity.
    """
    remaining = count
    while remaining > 0:
        burst_size = min(remaining, rng.randint(3, 8))
        remaining -= burst_size

        burst_start = random_timestamp_between(rng, attack_start, attack_end - timedelta(hours=1))
        device = gen_device_id(rng)
        ip = gen_ip(rng)

        for i in range(burst_size):
            ts = burst_start + timedelta(seconds=rng.randint(5, 60 * 10))
            user = gen_user_id(rng)
            # Higher-than-baseline amount but not always enormous.
            amount = round(rng.uniform(2_000, 25_000), 2)
            status = weighted_status(rng, force_failed=(rng.random() < 0.3))
            txn = _basic_txn_fields(rng, ts, user, device, ip, amount, status)
            txn["fraud_scenario"] = "combined"
            txns.append(txn)


# ----------------------------------------------------------------------------
# Main generation pipeline
# ----------------------------------------------------------------------------

def generate(rows: int, fraud_rate: float, seed: int,
             out_path: Path, metadata_path: Path) -> Dict:
    rng = random.Random(seed)

    start_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    attack_start = start_time + timedelta(days=WARMUP_DAYS)
    end_time = start_time + timedelta(days=TOTAL_DAYS)

    # Target counts.
    target_fraud = int(round(rows * fraud_rate))
    target_legit = rows - target_fraud

    # Build population.
    users, merchants, shared_devices, shared_ips = build_population(rng, start_time, target_legit)

    # Legit transactions.
    legit_txns = gen_legit_transactions(rng, users, merchants, start_time, end_time, target_legit)

    # Allocate fraud across scenarios according to SCENARIO_WEIGHTS.
    scenario_counts: Dict[str, int] = {}
    allocated = 0
    for name, w in SCENARIO_WEIGHTS.items():
        c = int(round(target_fraud * w))
        scenario_counts[name] = c
        allocated += c
    # Correct rounding drift on the largest scenario.
    scenario_counts["combined"] += target_fraud - allocated

    fraud_txns: List[Dict] = []
    inject_device_velocity(rng, fraud_txns, attack_start, end_time, scenario_counts["device_velocity"])
    inject_account_velocity(rng, fraud_txns, attack_start, end_time, scenario_counts["account_velocity"])
    inject_ip_concentration(rng, fraud_txns, attack_start, end_time, scenario_counts["ip_concentration"])
    inject_amount_anomaly(rng, fraud_txns, attack_start, end_time, scenario_counts["amount_anomaly"], users)
    inject_geo_anomaly(rng, fraud_txns, attack_start, end_time, scenario_counts["geo_anomaly"], users)
    inject_combined(rng, fraud_txns, attack_start, end_time, scenario_counts["combined"])

    all_txns = legit_txns + fraud_txns

    # Chronological sort. We break ties deterministically by transaction_id to
    # keep the output reproducible.
    all_txns.sort(key=lambda t: (t["timestamp"], t["transaction_id"]))

    # Trim or pad to exactly `rows` if rounding pushed us off slightly.
    if len(all_txns) > rows:
        # Drop trailing legit transactions to preserve fraud count.
        excess = len(all_txns) - rows
        kept = []
        dropped = 0
        for t in reversed(all_txns):
            if dropped < excess and not t["is_fraud"]:
                dropped += 1
                continue
            kept.append(t)
        all_txns = list(reversed(kept))
    elif len(all_txns) < rows:
        # Pad with extra legit transactions to hit exact row count.
        deficit = rows - len(all_txns)
        extra = gen_legit_transactions(rng, users, merchants, start_time, end_time, deficit)
        all_txns.extend(extra)
        all_txns.sort(key=lambda t: (t["timestamp"], t["transaction_id"]))

    # Write CSV.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "transaction_id", "timestamp", "user_id", "merchant_id",
        "device_fingerprint", "ip_address", "payment_method",
        "transaction_amount", "currency", "latitude", "longitude",
        "transaction_status", "account_creation_timestamp",
        "payment_attempt_number", "transaction_type",
        "is_fraud", "fraud_scenario",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in all_txns:
            row = dict(t)
            row["timestamp"] = t["timestamp"].isoformat()
            row["account_creation_timestamp"] = t["account_creation_timestamp"].isoformat()
            row["latitude"] = f"{t['latitude']:.6f}"
            row["longitude"] = f"{t['longitude']:.6f}"
            row["is_fraud"] = "true" if t["is_fraud"] else "false"
            writer.writerow(row)

    # Compute metadata + data quality report.
    total = len(all_txns)
    fraud_n = sum(1 for t in all_txns if t["is_fraud"])
    legit_n = total - fraud_n
    actual_rate = fraud_n / total if total else 0.0

    unique_users = len({t["user_id"] for t in all_txns})
    unique_devices = len({t["device_fingerprint"] for t in all_txns})
    unique_ips = len({t["ip_address"] for t in all_txns})
    unique_merchants = len({t["merchant_id"] for t in all_txns})

    scenario_dist = {name: 0 for name in SCENARIO_WEIGHTS}
    scenario_dist["none"] = 0
    for t in all_txns:
        scenario_dist[t["fraud_scenario"]] += 1

    amounts = [t["transaction_amount"] for t in all_txns]
    amount_mean = sum(amounts) / len(amounts)
    amount_median = sorted(amounts)[len(amounts) // 2]
    amount_var = sum((a - amount_mean) ** 2 for a in amounts) / len(amounts)
    amount_std = math.sqrt(amount_var)
    amount_min = min(amounts)
    amount_max = max(amounts)

    metadata = {
        "generation_params": {
            "rows_requested": rows,
            "seed": seed,
            "fraud_rate_requested": fraud_rate,
            "warmup_days": WARMUP_DAYS,
            "attack_days": ATTACK_DAYS,
        },
        "actual_counts": {
            "total_rows": total,
            "fraud": fraud_n,
            "legitimate": legit_n,
            "actual_fraud_rate": actual_rate,
        },
        "entities": {
            "unique_users": unique_users,
            "unique_devices": unique_devices,
            "unique_ips": unique_ips,
            "unique_merchants": unique_merchants,
            "legitimate_shared_devices": len(shared_devices),
            "legitimate_shared_ips": len(shared_ips),
        },
        "timeline": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "warmup_start": start_time.isoformat(),
            "warmup_end": attack_start.isoformat(),
            "attack_start": attack_start.isoformat(),
            "attack_end": end_time.isoformat(),
            "warmup_duration_days": WARMUP_DAYS,
            "attack_duration_days": ATTACK_DAYS,
        },
        "fraud_scenario_distribution": {
            name: {
                "count": scenario_dist[name],
                "percentage": (scenario_dist[name] / total) if total else 0.0,
            }
            for name in scenario_dist
        },
        "amounts": {
            "mean": round(amount_mean, 2),
            "median": round(amount_median, 2),
            "std": round(amount_std, 2),
            "min": round(amount_min, 2),
            "max": round(amount_max, 2),
        },
        "schema": fieldnames,
        "notes": [
            "All identifiers are opaque UUID-derived tokens.",
            "fraud_scenario is metadata for validation only; it must not be "
            "used as a model feature.",
            "Fraud prevalence is a synthetic benchmark prevalence, not a "
            "real-world or Razorpay fraud prevalence.",
        ],
    }
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Sentinel Phase 1 raw event generator")
    p.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--fraud-rate", type=float, default=DEFAULT_FRAUD_RATE)
    p.add_argument("--out", type=str, default="data/generated/raw_events.csv")
    p.add_argument("--metadata", type=str, default="data/generated/raw_events_metadata.json")
    args = p.parse_args()

    out_path = Path(args.out)
    meta_path = Path(args.metadata)

    print("=" * 70)
    print("Sentinel — Phase 1: Raw Event Generator")
    print("=" * 70)
    print(f"Requested rows:        {args.rows}")
    print(f"Requested fraud rate:  {args.fraud_rate}")
    print(f"Seed:                  {args.seed}")
    print()

    meta = generate(args.rows, args.fraud_rate, args.seed, out_path, meta_path)

    print("RAW DATASET DATA QUALITY REPORT")
    print("-" * 70)
    print("Dataset")
    print(f"  total rows:              {meta['actual_counts']['total_rows']}")
    print(f"  fraud count:             {meta['actual_counts']['fraud']}")
    print(f"  legitimate count:        {meta['actual_counts']['legitimate']}")
    print(f"  actual fraud rate:       {meta['actual_counts']['actual_fraud_rate']:.4%}")
    print(f"  requested fraud rate:    {meta['generation_params']['fraud_rate_requested']:.4%}")
    print()
    print("Entities")
    print(f"  unique users:            {meta['entities']['unique_users']}")
    print(f"  unique devices:          {meta['entities']['unique_devices']}")
    print(f"  unique IPs:              {meta['entities']['unique_ips']}")
    print(f"  unique merchants:        {meta['entities']['unique_merchants']}")
    print(f"  legit shared devices:    {meta['entities']['legitimate_shared_devices']}")
    print(f"  legit shared IPs:        {meta['entities']['legitimate_shared_ips']}")
    print()
    print("Timeline")
    print(f"  start:                   {meta['timeline']['start']}")
    print(f"  end:                     {meta['timeline']['end']}")
    print(f"  warm-up duration:        {meta['timeline']['warmup_duration_days']} days")
    print(f"  attack duration:         {meta['timeline']['attack_duration_days']} days")
    print()
    print("Fraud scenario distribution")
    for name, info in meta["fraud_scenario_distribution"].items():
        print(f"  {name:<20} count={info['count']:<6} pct={info['percentage']:.4%}")
    print()
    print("Amounts")
    print(f"  mean:   {meta['amounts']['mean']}")
    print(f"  median: {meta['amounts']['median']}")
    print(f"  std:    {meta['amounts']['std']}")
    print(f"  min:    {meta['amounts']['min']}")
    print(f"  max:    {meta['amounts']['max']}")
    print()
    print(f"Wrote raw events:    {out_path}")
    print(f"Wrote metadata:      {meta_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
