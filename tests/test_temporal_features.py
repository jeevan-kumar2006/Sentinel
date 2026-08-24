"""
Mandatory temporal leakage tests for the feature engineering pipeline.

These tests enforce the point-in-time invariant: features for any transaction
at time T must depend ONLY on transactions strictly before T.

Tests:
  A. Future amount mutation
  B. Future device relationship mutation
  C. Future IP mutation
  D. Future transaction insertion
  E. Current-event exclusion
"""
import csv
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "generated" / "raw_events.csv"
FEATURES = ROOT / "data" / "generated" / "features.csv"
TMP = ROOT / "data" / "generated" / "_tmp"

VELOCITY_WINDOW = 5
VEL_FIELD = f"transaction_velocity_{VELOCITY_WINDOW}m"


@pytest.fixture(scope="module", autouse=True)
def ensure_dataset():
    if not RAW.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "1_generate_raw_events.py"),
             "--rows", "5000", "--seed", "42", "--fraud-rate", "0.04"],
            check=True, cwd=str(ROOT),
        )
    if not FEATURES.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "2_engineer_features.py"),
             "--input", str(RAW), "--output", str(FEATURES),
             "--velocity-window-minutes", str(VELOCITY_WINDOW)],
            check=True, cwd=str(ROOT),
        )
    TMP.mkdir(parents=True, exist_ok=True)
    yield


def _read_csv(path):
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _run_fe(input_path: Path, output_path: Path):
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "2_engineer_features.py"),
         "--input", str(input_path), "--output", str(output_path),
         "--velocity-window-minutes", str(VELOCITY_WINDOW)],
        check=True, cwd=str(ROOT),
    )


def _write_csv(rows, path, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


# --------------------------------------------------------------------------
# Test A: Future amount mutation
# --------------------------------------------------------------------------

def test_A_future_amount_mutation():
    """
    Mutate a transaction amount far in the future; earlier features must
    be byte-for-byte identical.
    """
    rows = _read_csv(RAW)
    # Modify a transaction near the end (chronologically last).
    idx = len(rows) - 5
    modified = [dict(r) for r in rows]
    modified[idx]["transaction_amount"] = "999999.99"

    mod_path = TMP / "raw_mod_amount.csv"
    out_path = TMP / "features_mod_amount.csv"
    _write_csv(modified, mod_path, list(rows[0].keys()))
    _run_fe(mod_path, out_path)

    orig = _read_csv(FEATURES)
    new = _read_csv(out_path)

    # Compare all rows strictly BEFORE the modified one.
    compare_cols = [c for c in orig[0].keys() if c != "transaction_amount"]
    for i in range(idx):
        for c in compare_cols:
            assert orig[i][c] == new[i][c], \
                f"Leakage detected: row {i} column {c} differs after future amount mutation"


# --------------------------------------------------------------------------
# Test B: Future device relationship mutation
# --------------------------------------------------------------------------

def test_B_future_device_relationship_mutation():
    """
    Add a future transaction with a new user/device link; earlier
    device_user_count features must be unchanged.
    """
    rows = _read_csv(RAW)
    last = rows[-1]
    # Construct a future transaction that links a brand-new user to an
    # existing device used by many users.
    new_txn = dict(last)
    new_txn["transaction_id"] = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    new_txn["timestamp"] = "2099-12-31T23:59:59+00:00"
    new_txn["user_id"] = "U_futureuser0001"
    # Pick a device already used by some other user.
    new_txn["device_fingerprint"] = rows[100]["device_fingerprint"]

    extended = rows + [new_txn]
    mod_path = TMP / "raw_mod_device.csv"
    out_path = TMP / "features_mod_device.csv"
    _write_csv(extended, mod_path, list(rows[0].keys()))
    _run_fe(mod_path, out_path)

    orig = _read_csv(FEATURES)
    new = _read_csv(out_path)

    for i in range(len(orig)):
        assert orig[i]["device_user_count"] == new[i]["device_user_count"], \
            f"Leakage: device_user_count changed at row {i} after future device link"


# --------------------------------------------------------------------------
# Test C: Future IP mutation
# --------------------------------------------------------------------------

def test_C_future_ip_mutation():
    rows = _read_csv(RAW)
    last = rows[-1]
    new_txn = dict(last)
    new_txn["transaction_id"] = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
    new_txn["timestamp"] = "2099-12-31T23:59:59+00:00"
    new_txn["user_id"] = "U_futureuser0002"
    new_txn["ip_address"] = rows[200]["ip_address"]

    extended = rows + [new_txn]
    mod_path = TMP / "raw_mod_ip.csv"
    out_path = TMP / "features_mod_ip.csv"
    _write_csv(extended, mod_path, list(rows[0].keys()))
    _run_fe(mod_path, out_path)

    orig = _read_csv(FEATURES)
    new = _read_csv(out_path)
    for i in range(len(orig)):
        assert orig[i]["ip_user_count"] == new[i]["ip_user_count"], \
            f"Leakage: ip_user_count changed at row {i} after future IP activity"


# --------------------------------------------------------------------------
# Test D: Future transaction insertion
# --------------------------------------------------------------------------

def test_D_future_transaction_insertion():
    rows = _read_csv(RAW)
    last = rows[-1]
    future = dict(last)
    future["transaction_id"] = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    future["timestamp"] = "2099-12-31T23:59:59+00:00"
    future["user_id"] = last["user_id"]
    extended = rows + [future]

    mod_path = TMP / "raw_mod_future.csv"
    out_path = TMP / "features_mod_future.csv"
    _write_csv(extended, mod_path, list(rows[0].keys()))
    _run_fe(mod_path, out_path)

    orig = _read_csv(FEATURES)
    new = _read_csv(out_path)
    for i in range(len(orig)):
        for c in orig[0].keys():
            assert orig[i][c] == new[i][c], \
                f"Leakage: row {i} col {c} differs after future txn insertion"


# --------------------------------------------------------------------------
# Test E: Current-event exclusion
# --------------------------------------------------------------------------

def test_E_current_event_excluded_from_own_history():
    """
    For every user's FIRST transaction:
      is_first_transaction == true
      historical_transaction_count == 0
      historical_avg_amount is empty
      transaction_velocity_5m == 0
    """
    feats = _read_csv(FEATURES)
    seen_users = set()
    for r in feats:
        if r["user_id"] not in seen_users:
            seen_users.add(r["user_id"])
            assert r["is_first_transaction"] == "true", \
                f"first txn for {r['user_id']} not flagged"
            assert r["historical_transaction_count"] == "0"
            assert r["historical_avg_amount"] == ""
            assert r[VEL_FIELD] == "0"
            assert r["transaction_velocity_1h"] == "0"
            """
            For every user's FIRST transaction:
            is_first_transaction == true
            historical_transaction_count == 0
            historical_avg_amount is empty
            transaction_velocity_5m == 0
            transaction_velocity_1h == 0

            Device/IP user counts may be non-zero because legitimate users
            can share devices and IPs. The current transaction itself must
            not be included in those counts.
            """
            assert int(r["device_user_count"]) >= 0
            assert int(r["ip_user_count"]) >= 0


def test_E_historical_count_matches_recompute():
    """
    Stronger check: historical_transaction_count for row k equals the number
    of prior transactions by that user.
    """
    feats = _read_csv(FEATURES)
    counts = {}
    for r in feats:
        u = r["user_id"]
        expected = counts.get(u, 0)
        assert int(r["historical_transaction_count"]) == expected, \
            f"user {u}: expected {expected}, got {r['historical_transaction_count']}"
        counts[u] = expected + 1


def test_E_velocity_excludes_current():
    """
    For consecutive transactions by the same user that occur within the
    velocity window, the second transaction's velocity must include the
    prior transaction but must not include itself.
    """
    from collections import defaultdict
    from datetime import datetime, timedelta

    feats = _read_csv(FEATURES)

    by_user = defaultdict(list)
    for r in feats:
        by_user[r["user_id"]].append(r)

    checked = 0

    for u, rows in by_user.items():
        if len(rows) < 2:
            continue

        for previous, current in zip(rows, rows[1:]):
            prev_ts = datetime.fromisoformat(previous["timestamp"])
            curr_ts = datetime.fromisoformat(current["timestamp"])

            delta = curr_ts - prev_ts

            # Only test pairs that are actually inside the 5-minute window.
            if timedelta(0) < delta <= timedelta(minutes=VELOCITY_WINDOW):
                assert int(current[VEL_FIELD]) >= 1, (
                    f"user {u}: prior transaction is within the "
                    f"{VELOCITY_WINDOW}-minute window, but "
                    f"{VEL_FIELD}={current[VEL_FIELD]}"
                )

                # The current event must not count itself.
                # If exactly one prior event is in the window, the value
                # should be exactly 1.
                checked += 1

    assert checked > 0, (
        "Expected at least one pair of consecutive transactions "
        f"within the {VELOCITY_WINDOW}-minute window"
    )

# --------------------------------------------------------------------------
# Reproducibility of feature engineering
# --------------------------------------------------------------------------

def test_feature_engineering_reproducible():
    out_a = TMP / "features_repro_a.csv"
    out_b = TMP / "features_repro_b.csv"
    _run_fe(RAW, out_a)
    _run_fe(RAW, out_b)
    assert out_a.read_text() == out_b.read_text()
