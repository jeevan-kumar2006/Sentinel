import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
import json
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


with TestClient(app) as client:

    def test_health():
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "healthy"
        assert data["model_loaded"] is True

        df = pd.read_csv(ROOT / "data" / "generated" / "features.csv")
        assert data["transaction_count"] == len(df)


    def test_dashboard_summary():
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200

        with open(ROOT / "reports" / "phase2_evaluation.json") as f:
            report = json.load(f)

        data = response.json()

        assert data["precision"] == report["test_results"]["metrics"]["precision"]


    def test_evaluation():
        response = client.get("/api/v1/dashboard/evaluation")
        assert response.status_code == 200

        data = response.json()

        assert "test_results" in data
        assert "metrics" in data["test_results"]


    def test_economics():
        response = client.get("/api/v1/dashboard/economics")
        assert response.status_code == 200

        with open(ROOT / "artifacts" / "threshold_config.json") as f:
            thresholds = json.load(f)

        data = response.json()

        assert data["review_threshold"] == thresholds["review_threshold"]
        assert data["block_threshold"] == thresholds["block_threshold"]


    def test_transactions():
        response = client.get("/api/v1/transactions?page=1&limit=5")

        assert response.status_code == 200

        data = response.json()

        assert data["page"] == 1
        assert data["limit"] == 5
        assert len(data["items"]) == 5

        # Test filter
        resp_filter = client.get(
            "/api/v1/transactions?risk_decision=BLOCK"
        )

        assert resp_filter.status_code == 200

        for item in resp_filter.json()["items"]:
            assert item["decision"] == "BLOCK"

        # Test search
        first_txn_id = data["items"][0]["transaction_id"]

        resp_search = client.get(
            f"/api/v1/transactions?search={first_txn_id}"
        )

        assert resp_search.status_code == 200
        assert len(resp_search.json()["items"]) == 1

        # Invalid pagination
        resp_invalid = client.get(
            "/api/v1/transactions?page=0"
        )

        assert resp_invalid.status_code == 422


    def test_transaction_detail():
        resp = client.get("/api/v1/transactions?limit=1")

        assert resp.status_code == 200

        txn_id = resp.json()["items"][0]["transaction_id"]

        response = client.get(
            f"/api/v1/transactions/{txn_id}"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["transaction_id"] == txn_id
        assert "risk_probability" in data
        assert "risk_score" in data
        assert "decision" in data
        assert "reasons" in data

        resp_404 = client.get(
            "/api/v1/transactions/invalid-id"
        )

        assert resp_404.status_code == 404


    def test_risk_score():
        resp = client.get("/api/v1/transactions?limit=1")

        assert resp.status_code == 200

        txn = resp.json()["items"][0]

        with open(ROOT / "artifacts" / "selected_features.json") as f:
            features = json.load(f)

        payload = {
            feat: txn.get(feat)
            for feat in features
        }

        payload["transaction_id"] = "test-txn-123"

        response = client.post(
            "/api/v1/risk/score",
            json=payload
        )

        assert response.status_code == 200

        data = response.json()

        assert 0 <= data["risk_probability"] <= 1
        assert 0 <= data["risk_score"] <= 100

        assert abs(
            data["risk_score"]
            - data["risk_probability"] * 100
        ) < 0.01

        assert data["decision"] in [
            "ALLOW",
            "REVIEW",
            "BLOCK",
        ]

        assert len(data["reasons"]) > 0

        resp_invalid = client.post(
            "/api/v1/risk/score",
            json={"foo": "bar"}
        )

        assert resp_invalid.status_code == 422


    def test_model_freeze():
        from backend.app.services.model_service import model_service

        with pytest.raises(RuntimeError):
            model_service.model.fit(None, None)

        with pytest.raises(RuntimeError):
            model_service.preprocessor.fit(None, None)