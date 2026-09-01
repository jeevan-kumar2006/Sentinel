# Sentinel — AI-Powered Merchant Risk Assessment System

> Defensive AI merchant-risk system for the Razorpay AI Buildathon (Track 02).

Sentinel is a complete fraud detection pipeline combining:
- Synthetic transaction dataset generation
- Temporal feature engineering with leakage safeguards
- Logistic Regression and HistGradientBoosting ML models
- Economic threshold optimization
- FastAPI REST backend
- React/Vite interactive dashboard
- **AI Investigator for transaction explanation** ✨ NEW

## Status

✅ **Phase 1-4.6: Complete** | 🎯 **Phase 5: AI Investigator (NEW)**

| Phase | Component | Tests | Status |
|-------|-----------|-------|--------|
| 1 | Data Foundation | 19/19 | ✅ |
| 2 | ML Engine & Evaluation | 22/22 | ✅ |
| 3 | FastAPI Backend | 30/30 | ✅ |
| 4 | Frontend Dashboard | + | ✅ |
| 4.5 | Merchant UX Redesign | + | ✅ |
| 4.6 | UI Semantic Cleanup | + | ✅ |
| 5 | **AI Investigator** | **20/20** | **✅ NEW** |

**Test Results:** 50/50 passing ✅ | TypeScript: No errors ✅ | Build: Success ✅

---

## What's New in Phase 5?

### AI Investigator

An evidence-based explanation system that helps merchants understand **why** specific transactions are flagged as high-risk.

**Key Features:**
- ✅ Explains decisions using **only verified Sentinel evidence**
- ✅ Google Gemini-powered explanations with fallback support
- ✅ Structured, merchant-friendly output
- ✅ Prompt injection defense
- ✅ 10-second timeout protection
- ✅ Never overrides ML model decisions
- ✅ Works without API key (deterministic fallback)

**Does NOT:**
- ❌ Change risk scores or routing decisions
- ❌ Infer customer identity or intent
- ❌ Access transaction history or external data
- ❌ Expose hidden fraud labels or ground truth

### New Endpoint

**POST** `/api/v1/investigator/{transaction_id}` — Get AI explanation for a transaction

```bash
curl -X POST http://127.0.0.1:8000/api/v1/investigator/txn_abc123
```

### New Frontend Feature

Transaction Detail page now includes **"AI Investigator"** section with on-demand investigation button.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Gemini API key (optional)

### Installation

```bash
# Install Python dependencies (includes google-genai)
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Set Gemini API key (optional)
export GEMINI_API_KEY="your_api_key_here"
```

### Run

```bash
# Terminal 1: Backend
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Access: http://127.0.0.1:5173
```

### Verify

```bash
# Run all tests
python -m pytest tests/ -v
# Expected: 50 passed ✅

# TypeScript check
cd frontend && npx tsc --noEmit && cd ..
# Expected: No errors ✅

# Production build
cd frontend && npm run build && cd ..
# Expected: Build successful ✅
```

---

## Architecture Overview

```
Transaction Input
    ↓
Sentinel ML Engine
├── risk_probability
├── risk_score
└── decision (ALLOW / REVIEW / BLOCK)
    ↓
Evidence Builder (NEW)
├── Compact, deterministic evidence
├── Never includes fraud labels
└── <10KB per transaction
    ↓
AI Investigator Provider (NEW)
├── GoogleGemini (if API key available)
└── Mock Provider (fallback)
    ↓
Structured Explanation (Pydantic validated)
├── summary
├── key_signals
├── recommendation
└── confidence & limitations
    ↓
React Frontend
└── Transaction Detail Page
```

---

## API Examples

### Get Transaction Detail with Reasons

```bash
curl http://127.0.0.1:8000/api/v1/transactions/txn_abc123
```

Response includes Sentinel risk signals (deterministic reason codes).

### Investigate Transaction (NEW)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/investigator/txn_abc123
```

**Success Response (with Gemini):**
```json
{
  "transaction_id": "txn_abc123",
  "available": true,
  "decision": "BLOCK",
  "risk_score": 94.2,
  "risk_probability": 0.942,
  "summary": "Multiple high-risk signals detected...",
  "key_signals": [
    {
      "signal": "High Device Sharing",
      "evidence": "Device used by 12 users"
    }
  ],
  "recommended_action": "Reject transaction per policy.",
  "explanation_confidence": "high",
  "limitations": [...]
}
```

**Fallback Response (no Gemini):**
```json
{
  "available": false,
  "summary": "AI investigation unavailable.",
  "key_signals": [...deterministic signals...],
  "explanation_confidence": "not_available"
}
```

---

## Implementation Details

### Backend Components (NEW in Phase 5)

| File | Purpose |
|------|---------|
| `backend/app/services/evidence_service.py` | Builds compact transaction evidence |
| `backend/app/services/investigator_service.py` | LLM provider abstraction (Mock/Gemini) |
| `backend/app/api/endpoints/investigator.py` | API endpoint orchestration |
| `backend/app/schemas/investigator.py` | Pydantic schemas for validation |

### Frontend Components (UPDATED in Phase 5)

| File | Changes |
|------|---------|
| `frontend/src/pages/TransactionDetailPage.tsx` | Added AI Investigator section |
| `frontend/src/services/api.ts` | Added `investigateTransaction()` |
| `frontend/src/types/api.ts` | Added `InvestigatorResponse` type |

### Tests (NEW)

| File | Tests |
|------|-------|
| `tests/test_investigator.py` | 20 tests covering evidence, providers, endpoints, security |

---

## Environment Variables

```bash
# OPTIONAL: Enable AI Investigator with Google Gemini
export GEMINI_API_KEY="your_api_key_here"

# Works without this variable (uses mock provider)
```

⚠️ **Never commit `.env` files or API keys to Git**

---

## Key Security Features

### Evidence Integrity
- ✅ Deterministic output (same input = same output)
- ✅ Structured JSON serialization only
- ✅ Maximum 10KB payload per transaction
- ✅ No hidden labels or ground truth

### Prompt Injection Defense
- ✅ Transaction data never in system instruction
- ✅ All transaction fields treated as untrusted
- ✅ Explicit evidence delimiters in prompt
- ✅ System instruction explicitly rejects embedded commands

### Timeout & Reliability
- ✅ 10-second maximum timeout for Gemini
- ✅ Graceful fallback when API unavailable
- ✅ Schema validation of all responses
- ✅ Rejection of contradictory outputs
- ✅ Sentinel decision always preserved

---

## Testing

### Run All Tests
```bash
python -m pytest tests/ -v
# 50 tests: 8 API + 20 Investigator + 22 ML
```

### Run Investigator Tests Only
```bash
python -m pytest tests/test_investigator.py -v
```

### Evidence Builder Tests
```python
# Verifies:
# ✅ Deterministic output
# ✅ Excludes is_fraud
# ✅ Excludes fraud_scenario
# ✅ No large arrays
# ✅ Compact payload
# ✅ Safe NaN handling
```

### Provider Tests
```python
# Verifies:
# ✅ Mock provider returns valid investigations
# ✅ Gemini provider contradiction detection
# ✅ Factory returns correct provider type
# ✅ Fallback behavior
```

### Endpoint Tests
```python
# Verifies:
# ✅ 404 for invalid transaction
# ✅ Valid response schema
# ✅ Authoritative fields from Sentinel only
# ✅ Deterministic recommended actions
# ✅ Graceful fallback
```

### Integration Tests
```python
# Verifies:
# ✅ Existing API contracts unchanged
# ✅ Dashboard endpoints still work
# ✅ Prompt injection defense
```

---

## Troubleshooting

### "Transaction service has not been loaded"
Ensure the FastAPI app starts and loads data:
```bash
# Check uvicorn startup messages
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### TypeScript errors in frontend
```bash
cd frontend
npm install
npx tsc --noEmit
cd ..
```

### Gemini API errors
1. Check API key: `echo $GEMINI_API_KEY`
2. Verify permissions at console.cloud.google.com
3. Fall back to mock provider (remove API key): `unset GEMINI_API_KEY`

### Tests failing
```bash
# Ensure all dependencies installed
pip install -r requirements.txt --upgrade

# Run with verbose output
python -m pytest tests/ -vv --tb=short
```

---

## Important Notes

### ML Model Authority
Sentinel's ML model is the **sole authority** for risk assessment:
- `risk_probability` — Fraud likelihood from model
- `risk_score` — Probability × 100
- `decision` — ALLOW / REVIEW / BLOCK routing
- Fraud classification

The AI Investigator **only explains** these values. It never recalculates or overrides them.

### Synthetic Data
- ~4% fraud rate is a **synthetic benchmark** for evaluation
- NOT representative of production fraud rates
- Used to provide enough positive examples for testing

### No Database
- All data reloaded on server restart
- Suitable for hackathon/demo
- Production deployment would require PostgreSQL

---

## File Structure

```
Sentinel/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/endpoints/
│   │   │   ├── investigator.py ⭐ NEW
│   │   │   ├── health.py
│   │   │   ├── dashboard.py
│   │   │   ├── risk.py
│   │   │   └── transactions.py
│   │   ├── schemas/
│   │   │   ├── investigator.py ⭐ NEW
│   │   │   └── ...
│   │   ├── services/
│   │   │   ├── evidence_service.py ⭐ NEW
│   │   │   ├── investigator_service.py ⭐ NEW
│   │   │   └── ...
│   │   └── ...
│   └── ml/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── TransactionDetailPage.tsx ⭐ UPDATED
│   │   │   └── ...
│   │   ├── services/
│   │   │   └── api.ts ⭐ UPDATED
│   │   ├── types/
│   │   │   └── api.ts ⭐ UPDATED
│   │   └── ...
│   └── ...
├── tests/
│   ├── test_investigator.py ⭐ NEW
│   └── ...
├── requirements.txt ⭐ UPDATED (added google-genai)
└── README.md ⭐ UPDATED
```

---

## Performance

| Metric | Value |
|--------|-------|
| Evidence payload | <10KB |
| Gemini timeout | 10 seconds |
| Mock response time | <1ms |
| Frontend build | ~570KB |
| Frontend gzipped | ~163KB |

---

## Next Steps (Phase 6+)

- 🔒 Authentication & Authorization
- 💾 Persistent data layer (PostgreSQL)
- 📊 Batch analysis & Shadow Mode
- 📈 Merchant feedback loop
- 🤖 Multi-model ensembles

---

## Support

For issues or questions about Phase 5 implementation:
1. Check test coverage: `python -m pytest tests/test_investigator.py -v`
2. Verify environment: `echo $GEMINI_API_KEY` / `unset GEMINI_API_KEY`
3. Check logs: Look at uvicorn terminal output

---

**Sentinel Phases 1-5** | Built for Razorpay AI Buildathon 2024 | Last updated: 2026-09-01

Files
sentinel/├── scripts/│   ├── 1_generate_raw_events.py│   └── 2_engineer_features.py├── data/generated/│   ├── raw_events.csv│   ├── raw_events_metadata.json│   ├── features.csv│   └── feature_metadata.json├── tests/│   ├── test_raw_generation.py│   └── test_temporal_features.py└── README.md
Quick start
python scripts/1_generate_raw_events.py \    --rows 50000 \    --seed 42 \    --fraud-rate 0.04python scripts/2_engineer_features.py \    --input data/generated/raw_events.csv \    --output data/generated/features.csv \    --velocity-window-minutes 5pytest tests/ -v
