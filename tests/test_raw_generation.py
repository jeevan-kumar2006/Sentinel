"""
Tests for the raw event generator.

Run with:  pytest tests/test_raw_generation.py -v
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "generated" / "raw_events.csv"
META = ROOT / "data" / "generated" / "raw_events_metadata.json"

FORBIDDEN_SUBSTRINGS = [
    "fraud", "attacker", "attack", "bot", "normal",
    "suspicious", "legitimate", "fake", "malicious",
]


@pytest.fixture(scope="module", autouse=True)
def ensure_dataset():
    if not RAW.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "1_generate_raw_events.py"),
             "--rows", "5000", "--seed", "42", "--fraud-rate", "0.04"],
            check=True, cwd=str(ROOT),
        )
    yield


def _read_raw():
    with RAW.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_raw_csv_exists_and_nonempty():
    assert RAW.exists(), "raw_events.csv must exist"
    rows = _read_raw()
    assert len(rows) > 0


def test_required_columns_present():
    rows = _read_raw()
    required = {
        "transaction_id", "timestamp", "user_id", "merchant_id",
        "device_fingerprint", "ip_address", "payment_method",
        "transaction_amount", "currency", "latitude", "longitude",
        "transaction_status", "account_creation_timestamp",
        "payment_attempt_number", "transaction_type",
        "is_fraud", "fraud_scenario",
    }
    assert required.issubset(set(rows[0].keys()))


def test_chronological_order():
    rows = _read_raw()
    timestamps = [r["timestamp"] for r in rows]
    assert timestamps == sorted(timestamps)


def test_warmup_precedes_attack():
    with META.open("r") as f:
        meta = json.load(f)
    warmup_end = meta["timeline"]["warmup_end"]
    attack_start = meta["timeline"]["attack_start"]
    assert warmup_end == attack_start


def test_no_fraud_in_warmup_period():
    rows = _read_raw()
    with META.open("r") as f:
        meta = json.load(f)
    warmup_end = meta["timeline"]["warmup_end"]
    for r in rows:
        if r["timestamp"] < warmup_end:
            assert r["is_fraud"] == "false", \
                "Warm-up must not contain fraud (date must not be a fraud signal)"


def test_attack_window_contains_both_classes():
    rows = _read_raw()
    with META.open("r") as f:
        meta = json.load(f)
    attack_start = meta["timeline"]["attack_start"]
    attack_rows = [r for r in rows if r["timestamp"] >= attack_start]
    fraud = any(r["is_fraud"] == "true" for r in attack_rows)
    legit = any(r["is_fraud"] == "false" for r in attack_rows)
    assert fraud and legit, "Attack window must contain both fraud and legit transactions"


def test_actual_fraud_rate_within_tolerance():
    rows = _read_raw()
    n = len(rows)
    n_fraud = sum(1 for r in rows if r["is_fraud"] == "true")
    rate = n_fraud / n
    # Tolerance ±0.5% absolute.
    assert abs(rate - 0.04) < 0.005, f"actual rate {rate} outside tolerance"


def test_no_semantic_identifiers():
    rows = _read_raw()
    id_fields = ["transaction_id", "user_id", "merchant_id",
                 "device_fingerprint", "ip_address"]
    for r in rows:
        for f in id_fields:
            val = r[f].lower()
            for bad in FORBIDDEN_SUBSTRINGS:
                assert bad not in val, f"forbidden substring '{bad}' in {f}={r[f]}"


def test_all_scenarios_present():
    rows = _read_raw()
    scenarios_seen = {r["fraud_scenario"] for r in rows if r["is_fraud"] == "true"}
    required = {"device_velocity", "account_velocity", "ip_concentration",
                "amount_anomaly", "geo_anomaly", "combined"}
    assert required.issubset(scenarios_seen)


def test_metadata_matches_csv():
    rows = _read_raw()
    with META.open("r") as f:
        meta = json.load(f)
    assert meta["actual_counts"]["total_rows"] == len(rows)
    assert meta["actual_counts"]["fraud"] == sum(1 for r in rows if r["is_fraud"] == "true")


def test_reproducibility_same_seed():
    """Same seed must produce identical raw events."""
    out_a = ROOT / "data" / "generated" / "_repro_a.csv"
    out_b = ROOT / "data" / "generated" / "_repro_b.csv"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "1_generate_raw_events.py"),
         "--rows", "2000", "--seed", "123", "--fraud-rate", "0.04",
         "--out", str(out_a)],
        check=True, cwd=str(ROOT),
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "1_generate_raw_events.py"),
         "--rows", "2000", "--seed", "123", "--fraud-rate", "0.04",
         "--out", str(out_b)],
        check=True, cwd=str(ROOT),
    )
    assert out_a.read_text() == out_b.read_text()
    out_a.unlink()
    out_b.unlink()
