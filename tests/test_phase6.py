import pytest
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from backend.ml.data import load_data
from backend.ml.economics import EconomicModel
import json
import os
import logging
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.investigator import AIInvestigation, KeySignal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(scope="module", autouse=True)
def client():
    with TestClient(app) as c:
        yield c

class TestPhase6Hardening:
    def test_scoring_logs_match_response(self, client, caplog):
        """Task 4: Structured logging matches API response and contains required fields."""
        txns_response = client.get("/api/v1/transactions?limit=1")
        assert txns_response.status_code == 200
        txn = txns_response.json()["items"][0]
        
        with open(ROOT / "artifacts" / "selected_features.json") as f:
            features = json.load(f)
            
        payload = {feat: txn.get(feat) for feat in features}
        payload["transaction_id"] = "test-txn-logging"
        
        with caplog.at_level(logging.INFO, logger="sentinel.scoring"):
            response = client.post("/api/v1/risk/score", json=payload)
            
        assert response.status_code == 200
        data = response.json()
        
        # Find the specific log record
        log_record = next(r for r in caplog.records if r.name == "sentinel.scoring" and r.message == "Transaction scored")
        
        # Verify required fields are logged
        assert hasattr(log_record, "transaction_id")
        assert hasattr(log_record, "risk_probability")
        assert hasattr(log_record, "risk_score")
        assert hasattr(log_record, "review_threshold")
        assert hasattr(log_record, "block_threshold")
        assert hasattr(log_record, "decision")
        
        # Verify logged values match API response
        assert log_record.transaction_id == "test-txn-logging"
        assert log_record.risk_probability == data["risk_probability"]
        assert log_record.risk_score == data["risk_score"]
        assert log_record.decision == data["decision"]

    def test_investigator_failure_wording_and_authority(self, client):
        """Task 3: Safe Investigator failure handling and authoritative fields."""
        txns_response = client.get("/api/v1/transactions?limit=1")
        assert txns_response.status_code == 200
        original_txn = txns_response.json()["items"][0]
        txn_id = original_txn["transaction_id"]
        
        with patch('backend.app.api.endpoints.investigator.get_investigator_provider') as mock_provider:
            mock_provider.return_value.investigate = AsyncMock(side_effect=Exception("API Error"))
            response = client.post(f"/api/v1/investigator/{txn_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["available"] == False
            assert data["explanation_confidence"] == "not_available"
            
            # Verify exact safe wording
            assert data["summary"] == "AI explanation is temporarily unavailable. Sentinel's authoritative risk score and decision remain unchanged."
            
            # Verify authoritative fields remain unchanged
            assert data["decision"] == original_txn["decision"]
            assert data["risk_score"] == original_txn["risk_score"]
            assert data["risk_probability"] == original_txn["risk_probability"]
            assert data["transaction_id"] == txn_id

    def test_investigator_provider_timeout_fallback(self):
        """Provider-level test for Investigator failure/timeout path without real API request."""
        from backend.app.services.investigator_service import GeminiInvestigatorProvider
        import asyncio
        
        provider = GeminiInvestigatorProvider()
        
        with patch('backend.app.services.investigator_service.genai') as mock_genai:
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            
            # Simulate a timeout exception during generation
            mock_client.models.generate_content.side_effect = TimeoutError("Request timed out")
            
            with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
                evidence = {"transaction_id": "txn_123", "decision": "BLOCK", "risk_score": 99.0}
                investigation = asyncio.run(provider.investigate(evidence))
                
            # Should gracefully fallback to None on timeout
            assert investigation is None

    def test_missing_gemini_key_uses_safe_provider(self):
        from backend.app.services.investigator_service import MockInvestigatorProvider

        with patch.dict(os.environ, {}, clear=True):
            provider = __import__(
                'backend.app.services.investigator_service',
                fromlist=['get_investigator_provider'],
            ).get_investigator_provider()
        assert isinstance(provider, MockInvestigatorProvider)

    def test_gemini_rejects_unverified_signals(self):
        from backend.app.services.investigator_service import GeminiInvestigatorProvider

        investigation = AIInvestigation(
            summary="verified",
            key_signals=[KeySignal(signal="Invented", evidence="unknown behavior")],
            explanation_confidence="high",
            limitations=[],
        )
        assert GeminiInvestigatorProvider._signals_are_grounded(
            investigation,
            {"features": {"transaction_velocity_5m": 0}},
        ) is False

    def test_gemini_cannot_change_sentinel_decision(self, client):
        txn = client.get("/api/v1/transactions?page=1&limit=1").json()["items"][0]
        tampered = AIInvestigation(
            summary="The transaction should be blocked.",
            key_signals=[],
            explanation_confidence="high",
            limitations=[],
        )
        with patch('backend.app.api.endpoints.investigator.get_investigator_provider') as mock_provider:
            mock_provider.return_value.investigate = AsyncMock(return_value=tampered)
            response = client.post(f"/api/v1/investigator/{txn['transaction_id']}")
        assert response.json()["decision"] == txn["decision"]
        assert response.json()["recommended_action"] != "The transaction should be blocked."

    def test_no_ground_truth_in_investigator_evidence(self, client):
        """Verify malicious/internal fields never leak into evidence."""
        from backend.app.services.evidence_service import EvidenceBuilder
        
        malicious_txn = {
            "transaction_id": "txn_malicious",
            "timestamp": "2024-01-01T10:00:00",
            "transaction_amount": 100.0,
            "risk_score": 50.0,
            "risk_probability": 0.5,
            "decision": "ALLOW",
            "is_fraud": True,
            "fraud_scenario": "account_takeover",
            "train_split": True,
            "test_split": False,
            "secret_internal_field": "secret_data",
            "api_key": "1234567890abcdef",
            "historical_transactions": [1, 2, 3, 4, 5]
        }
        
        evidence = EvidenceBuilder.build_evidence(malicious_txn)
        ev_str = json.dumps(evidence)
        
        assert "is_fraud" not in ev_str
        assert "fraud_scenario" not in ev_str
        assert "train_split" not in ev_str
        assert "test_split" not in ev_str
        assert "secret_internal_field" not in ev_str
        assert "api_key" not in ev_str
        assert "historical_transactions" not in ev_str

    def test_threshold_sweep_uses_validation_only(self):
        """Verify threshold sweep is reproducible from validation data only."""
        with open(ROOT / "reports" / "phase2_evaluation.json") as f:
            report = json.load(f)

        sweep = report["validation_results"]["threshold_sweep"]

        assert len(sweep) == 20

        thresholds = [point["threshold"] for point in sweep]
        expected_thresholds = np.linspace(0.05, 0.95, 20)

        assert thresholds == pytest.approx(expected_thresholds.tolist())

        splits, _ = load_data()
        val_df = splits["validation"]

        with open(ROOT / "artifacts" / "selected_features.json") as f:
            features = json.load(f)

        with open(ROOT / "artifacts" / "threshold_config.json") as f:
            thresholds_config = json.load(f)

        preprocessor = joblib.load(ROOT / "artifacts" / "preprocessing.joblib")
        model = joblib.load(ROOT / "artifacts" / "selected_model.joblib")

        probs_val = model.predict_proba(
            preprocessor.transform(val_df[features])
        )[:, 1]

        review_t = thresholds_config["review_threshold"]
        economic_model = EconomicModel()

        for point, threshold in zip(sweep, expected_thresholds):
            val_pred = (probs_val >= threshold).astype(int)

            decisions = pd.Series("ALLOW", index=val_df.index)
            decisions[probs_val >= review_t] = "REVIEW"
            decisions[probs_val >= threshold] = "BLOCK"

            economics = economic_model.calculate_loss(
                val_df,
                decisions,
            )

            tn, fp, fn, tp = confusion_matrix(
                val_df["is_fraud"],
                val_pred,
            ).ravel()

            precision = precision_score(
                val_df["is_fraud"],
                val_pred,
                zero_division=0,
            )

            recall = recall_score(
                val_df["is_fraud"],
                val_pred,
                zero_division=0,
            )

            f1 = f1_score(
                val_df["is_fraud"],
                val_pred,
                zero_division=0,
            )

            routing = decisions.value_counts()

            assert point["threshold"] == pytest.approx(threshold)

            assert point["routing"] == {
                "allow": int(routing.get("ALLOW", 0)),
                "review": int(routing.get("REVIEW", 0)),
                "block": int(routing.get("BLOCK", 0)),
            }

            assert point["classification"]["basis"] == "BLOCK vs NOT-BLOCK"
            assert point["classification"]["precision"] == pytest.approx(precision)
            assert point["classification"]["recall"] == pytest.approx(recall)
            assert point["classification"]["f1"] == pytest.approx(f1)
            assert point["classification"]["tp"] == int(tp)
            assert point["classification"]["fp"] == int(fp)
            assert point["classification"]["fn"] == int(fn)
            assert point["classification"]["tn"] == int(tn)

            assert point["precision"] == pytest.approx(precision)
            assert point["recall"] == pytest.approx(recall)
            assert point["f1"] == pytest.approx(f1)

            assert point["economics"]["baseline_fraud_loss"] == pytest.approx(
                economics["baseline_fraud_loss"]
            )
            assert point["economics"]["residual_fraud_loss"] == pytest.approx(
                economics["residual_fraud_loss"]
            )
            assert point["economics"]["fraud_loss_prevented"] == pytest.approx(
                economics["fraud_loss_prevented"]
            )
            assert point["economics"]["false_positive_cost"] == pytest.approx(
                economics["false_positive_cost"]
            )
            assert point["economics"]["net_economic_benefit"] == pytest.approx(
                economics["net_economic_benefit"]
            )

            assert point["net_economic_benefit"] == pytest.approx(
                economics["net_economic_benefit"]
            )
