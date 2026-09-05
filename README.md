# Sentinel --- AI Risk Manager

> **Razorpay AI Buildathon 2026 --- Track 02: AI Risk Manager**
>
> Sentinel is a defensive transaction-risk platform for
> **velocity/anomaly-based transaction fraud**. It detects suspicious
> transactions, makes deterministic **ALLOW / REVIEW / BLOCK**
> decisions, measures economic impact, and provides a constrained AI
> Investigator that explains the decision without overriding it.

------------------------------------------------------------------------

# 🚀 HOW TO RUN THE PROJECT

> **This is the main quick-start section. Follow these steps in order.**

## Prerequisites

-   Python 3.11+
-   Node.js 18+
-   npm
-   Git
-   Windows PowerShell

## 1. Clone

``` powershell
git clone https://github.com/jeevan-kumar2006/Sentinel.git
cd Sentinel
```

## 2. Create and activate Python environment

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

## 3. Install backend dependencies

From the repository root:

``` powershell
pip install -r requirements.txt
```

## 4. Start the backend --- Terminal 1

``` powershell
cd C:\LocalAI\Sentinel
.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Backend:

``` text
http://127.0.0.1:8000
```

Health check:

``` text
http://127.0.0.1:8000/api/v1/health
```

Keep Terminal 1 running.

## 5. Start the frontend --- Terminal 2

``` powershell
cd C:\LocalAI\Sentinel\frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Frontend:

``` text
http://127.0.0.1:5173
```

Open that address in your browser.

## 6. Main application flow

``` text
Overview
   ↓
Evaluation
   ↓
Economics
   ↓
Transactions
   ↓
Transaction Detail
   ↓
AI Investigator
```

### If the UI says "API Offline"

Check that:

1.  Terminal 1 is running Uvicorn.
2.  Backend is on port `8000`.
3.  Frontend is on port `5173`.
4.  `http://127.0.0.1:8000/api/v1/health` responds.

## 7. Optional Gemini

Gemini is optional for the core risk engine.

``` powershell
$env:GEMINI_API_KEY="YOUR_ACTUAL_KEY"
```

Verify without printing the key:

``` powershell
if ($env:GEMINI_API_KEY) {
    "GEMINI_API_KEY_PRESENT"
} else {
    "GEMINI_API_KEY_MISSING"
}
```

Configured model:

``` text
gemini-2.5-flash-lite
```

Never commit or expose the key. Without it, the Investigator uses the
deterministic fallback.

## 8. Run tests

From the repository root:

``` powershell
python -m pytest tests\ -q
```

Final verified result:

``` text
49 passed
```

## 9. Production frontend build

``` powershell
cd C:\LocalAI\Sentinel\frontend
npm run build
```

Final verified result:

``` text
TypeScript compilation: PASS
Vite production build: PASS
```

------------------------------------------------------------------------

# 🗂️ COMPLETE REPOSITORY FOLDER STRUCTURE

The structure below reflects the **current `main` repository**,
including the nested backend/frontend directories and files that are
important to understanding the system.

``` text
Sentinel/
│
├── .gitignore
├── README.md
├── requirements.txt
│
├── artifacts/
│   └── selected_features.json
│
├── backend/
│   │
│   ├── app/
│   │   │
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   │
│   │   │   └── endpoints/
│   │   │       ├── dashboard.py
│   │   │       ├── health.py
│   │   │       ├── investigator.py
│   │   │       ├── risk.py
│   │   │       └── transactions.py
│   │   │
│   │   ├── core/
│   │   │   └── config.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── dashboard.py
│   │   │   ├── health.py
│   │   │   ├── investigator.py
│   │   │   ├── risk.py
│   │   │   └── transaction.py
│   │   │
│   │   └── services/
│   │       ├── evidence_service.py
│   │       ├── investigator_service.py
│   │       ├── model_service.py
│   │       ├── reason_service.py
│   │       └── transaction_service.py
│   │
│   └── ml/
│       ├── data.py
│       ├── economics.py
│       ├── evaluation.py
│       ├── models.py
│       ├── preprocessing.py
│       └── thresholds.py
│
├── data/
│   └── generated/
│       ├── feature_metadata.json
│       ├── features.csv
│       ├── raw_events.csv
│       └── raw_events_metadata.json
│
├── frontend/
│   │
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── vite.config.ts
│   │
│   └── src/
│       ├── App.tsx
│       ├── index.css
│       ├── main.tsx
│       ├── vite-env.d.ts
│       │
│       ├── components/
│       │   ├── charts/
│       │   │   ├── ConfusionMatrixChart.tsx
│       │   │   └── RoutingChart.tsx
│       │   │
│       │   ├── layout/
│       │   │   ├── Header.tsx
│       │   │   ├── Layout.tsx
│       │   │   └── Sidebar.tsx
│       │   │
│       │   ├── transactions/
│       │   │   ├── ReasonCodeList.tsx
│       │   │   └── TransactionTable.tsx
│       │   │
│       │   └── ui/
│       │       ├── Badge.tsx
│       │       ├── Card.tsx
│       │       ├── ErrorState.tsx
│       │       ├── LoadingState.tsx
│       │       ├── MetricCard.tsx
│       │       └── RiskBar.tsx
│       │
│       ├── pages/
│       │   ├── DashboardPage.tsx
│       │   ├── EconomicsPage.tsx
│       │   ├── EvaluationPage.tsx
│       │   ├── TransactionDetailPage.tsx
│       │   └── TransactionsPage.tsx
│       │
│       ├── services/
│       │   └── api.ts
│       │
│       ├── types/
│       │   └── api.ts
│       │
│       └── utils/
│           ├── dates.ts
│           └── format.ts
│
├── reports/
│   └── phase2_evaluation.json
│
├── scripts/
│   ├── 1_generate_raw_events.py
│   ├── 2_engineer_features.py
│   ├── 3_run_phase2.py
│   └── 4_generate_curves.py
│
└── tests/
    ├── test_api.py
    ├── test_investigator.py
    ├── test_phase2.py
    ├── test_phase6.py
    ├── test_raw_generation.py
    └── test_temporal_features.py
```

### What each major area does

  -----------------------------------------------------------------------
  Directory                           Responsibility
  ----------------------------------- -----------------------------------
  `artifacts/`                        Frozen feature/model/evaluation
                                      configuration artifacts

  `backend/app/api/`                  FastAPI routing and HTTP endpoints

  `backend/app/core/`                 Application configuration

  `backend/app/schemas/`              Pydantic request/response contracts

  `backend/app/services/`             Risk, transaction, evidence,
                                      reasoning and Investigator services

  `backend/ml/`                       Data loading, model, preprocessing,
                                      evaluation, thresholds and
                                      economics

  `data/generated/`                   Synthetic benchmark events and
                                      engineered features

  `frontend/src/components/`          Reusable dashboard components

  `frontend/src/pages/`               Main dashboard screens

  `frontend/src/services/`            Frontend API client

  `frontend/src/types/`               TypeScript API contracts

  `frontend/src/utils/`               Formatting/date helpers

  `reports/`                          Evaluation report artifacts

  `scripts/`                          Data generation, feature
                                      engineering, evaluation and
                                      threshold-curve scripts

  `tests/`                            Backend, temporal-feature, API,
                                      Investigator and Phase 6 regression
                                      tests
  -----------------------------------------------------------------------

> `.venv/`, `frontend/node_modules/`, and `frontend/dist/` are
> local/generated directories and are not part of the source structure
> shown above.

------------------------------------------------------------------------

# 🏗️ ARCHITECTURE DIAGRAM

``` text
                    ┌──────────────────────────────────┐
                    │  SYNTHETIC TRANSACTION EVENTS   │
                    │        Benchmark Dataset         │
                    └───────────────┬──────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────────┐
                    │   Point-in-Time Feature Engine   │
                    │                                  │
                    │ Velocity • Amount • Device • IP │
                    │ Geography • History • Attempts  │
                    └───────────────┬──────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────────┐
                    │       Frozen Preprocessing       │
                    │       Train-fitted pipeline      │
                    └───────────────┬──────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────────┐
                    │       FROZEN ML RISK MODEL       │
                    │   HistGradientBoostingClassifier │
                    └───────────────┬──────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────────┐
                    │        Risk Probability          │
                    │          ↓ Risk Score             │
                    │             0–100                 │
                    └───────────────┬──────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────────┐
                    │  DETERMINISTIC FROZEN POLICY     │
                    │                                  │
                    │  <20%       → ALLOW              │
                    │  20–<50%    → REVIEW             │
                    │  ≥50%       → BLOCK              │
                    └───────┬──────────┬───────────┬───┘
                            │          │           │
                            ▼          ▼           ▼
                         ALLOW      REVIEW       BLOCK
                            │          │           │
                            └──────────┼───────────┘
                                       ▼
                    ┌──────────────────────────────────┐
                    │       ECONOMIC EVALUATION         │
                    │                                  │
                    │ Baseline Loss                    │
                    │ Residual Loss                    │
                    │ Loss Prevented                   │
                    │ False-Positive Cost              │
                    │ Net Economic Benefit             │
                    └──────────────────────────────────┘


       ┌─────────────────────────────────────────────────────────┐
       │                 EXPLANATION LAYER                       │
       │                                                         │
       │  Allowlisted transaction evidence                       │
       │                  │                                      │
       │                  ▼                                      │
       │        ┌───────────────────────┐                        │
       │        │    AI Investigator    │                        │
       │        │   Gemini / Fallback   │                        │
       │        └───────────┬───────────┘                        │
       │                    │                                    │
       │                    ▼                                    │
       │          Human-readable explanation                     │
       │                                                         │
       │  AI cannot override risk probability, score, thresholds │
       │  or the authoritative ALLOW / REVIEW / BLOCK decision.  │
       └─────────────────────────────────────────────────────────┘
```

### Architecture principle

> **The ML + deterministic policy layer owns the decision. The AI
> Investigator only explains it.**

------------------------------------------------------------------------

# 1. BUILDATHON TRACK 02 ALIGNMENT

Track 02 asks for a working detector, verifier, or auto-responder for
**one class of loss**, measured precision and recall on a **held-out
test set**, honest metrics including **false-positive cost**, and a
**strictly defense-only** implementation.

  -----------------------------------------------------------------------
  Track requirement                   Sentinel implementation
  ----------------------------------- -----------------------------------
  Working                             Working transaction-fraud
  detector/verifier/auto-responder    detector + deterministic router

  One loss class                      Velocity/anomaly-based transaction
                                      fraud

  Held-out test set                   Chronological held-out test period

  Precision / recall                  Measured on final test set

  Honest metrics                      Precision, recall, F1, PR-AUC,
                                      ROC-AUC, confusion matrix, FP cost

  Financial impact                    Fraud loss prevented + net economic
                                      benefit

  Defense-only                        Yes
  -----------------------------------------------------------------------

**Defense-only:** Sentinel is designed only for defensive fraud-risk
detection, decision support, investigation, and loss reduction. It
contains no functionality intended to generate, evade, test, or
facilitate fraud.

------------------------------------------------------------------------

# 2. EXECUTIVE SUMMARY

Sentinel is built around one strict separation:

``` text
ML model
   ↓
Risk probability
   ↓
Risk score
   ↓
Deterministic frozen policy
   ↓
ALLOW / REVIEW / BLOCK

AI Investigator
   ↓
Explanation only
```

> **Sentinel makes the risk decision. AI explains the decision.**

------------------------------------------------------------------------

# 3. TEMPORAL ML DESIGN

Fraud detection can suffer from future leakage.

Sentinel uses point-in-time historical features and chronological
evaluation:

``` text
90-day warmup
      +
first 60% of attack window → TRAIN
next 20%                 → VALIDATION
final 20%                → TEST
```

The final test set is not used to select the production threshold.

------------------------------------------------------------------------

# 4. PRODUCTION FEATURE CONTRACT

The frozen production model uses:

``` text
transaction_amount
latitude
longitude
payment_attempt_number
is_first_transaction
has_historical_amount
has_previous_location
historical_transaction_count
historical_avg_amount
amount_ratio_to_history
transaction_velocity_5m
transaction_velocity_1h
time_since_previous_transaction
unique_devices_seen_before
unique_ips_seen_before
device_user_count
ip_user_count
failed_attempt_velocity
geographic_distance_from_previous
geographic_velocity
account_age_seconds
```

Primary model:

``` text
HistGradientBoostingClassifier
```

Baseline:

``` text
Logistic Regression
```

------------------------------------------------------------------------

# 5. HONEST EVALUATION

The benchmark is **synthetic**.

The audited synthetic split has approximately:

  Period         Fraud rate
  ------------ ------------
  Training        **2.15%**
  Validation        **26%**
  Test            **30.6%**

This is a known limitation of the synthetic generator. The later
validation/test periods represent an attack-heavy regime and are
materially different from training prevalence.

The final test set is approximately:

``` text
180 transactions
55 fraud cases
```

Recall:

``` text
47 / 55 = 0.8545
```

Approximate 95% Wilson interval:

``` text
73.8% – 92.4%
```

The test contains:

``` text
125 legitimate transactions
0 false positives
```

Therefore:

``` text
Precision = 1.0000
False-positive cost = ₹0
```

This is a property of the synthetic benchmark, **not a production
claim**.

------------------------------------------------------------------------

# 6. FROZEN TEST RESULTS

  Metric                  Result
  ----------------- ------------
  Precision           **1.0000**
  Recall              **0.8545**
  F1                  **0.9216**
  PR-AUC              **0.9961**
  ROC-AUC             **0.9981**
  True Negatives         **125**
  False Positives          **0**
  False Negatives          **8**
  True Positives          **47**

------------------------------------------------------------------------

# 7. ECONOMIC RESULTS

Current benchmark assumptions:

``` text
Chargeback fee = ₹1,500
Customer LTV   = ₹5,000
```

  Metric                          Result
  ---------------------- ---------------
  Baseline fraud loss      **₹6,05,610**
  Residual fraud loss        **₹28,712**
  Fraud loss prevented     **₹5,76,898**
  False-positive cost             **₹0**
  Net economic benefit     **₹5,76,898**

The current economic model does not assign an explicit analyst cost to
`REVIEW`; this is a documented future improvement.

------------------------------------------------------------------------

# 8. THRESHOLDS

    Risk probability Decision
  ------------------ ----------
            `< 0.20` `ALLOW`
     `0.20 – < 0.50` `REVIEW`
           `>= 0.50` `BLOCK`

The Economics page includes the validation-derived threshold sweep.

------------------------------------------------------------------------

# 9. AI INVESTIGATOR

The Investigator is an explanation layer, not a second fraud detector.

It provides:

-   summary
-   key signals
-   explanation confidence
-   limitations

It does not own:

-   risk probability
-   risk score
-   thresholds
-   ALLOW / REVIEW / BLOCK
-   ground truth

When configured, Gemini uses:

``` text
gemini-2.5-flash-lite
```

Ground-truth fields such as `is_fraud`, `fraud_scenario`, and
train/validation/test membership are excluded from Investigator
evidence.

Contradictory or unsupported AI output is rejected, and the
deterministic fallback remains available.

------------------------------------------------------------------------

# 10. APPLICATION PAGES

### Overview

Operational risk summary.

### Evaluation

Precision, recall, F1, PR-AUC, ROC-AUC and confusion matrix.

### Economics

Thresholds, loss, prevented loss, false-positive cost, net benefit and
trade-off curve.

### Transactions

Transaction-level routing.

### Transaction Detail

Transaction context and deterministic evidence.

### AI Investigator

Human-readable explanation without decision authority.

------------------------------------------------------------------------

# 11. API

Base URL:

``` text
http://127.0.0.1:8000
```

  Method   Endpoint
  -------- -----------------------------------------
  GET      `/api/v1/health`
  GET      `/api/v1/dashboard/summary`
  GET      `/api/v1/dashboard/evaluation`
  GET      `/api/v1/dashboard/economics`
  GET      `/api/v1/transactions`
  GET      `/api/v1/transactions/{transaction_id}`
  POST     `/api/v1/risk/score`
  POST     `/api/v1/investigator/{transaction_id}`

------------------------------------------------------------------------

# 12. KNOWN LIMITATIONS AND NEXT STEPS

-   Synthetic data is not real Razorpay traffic.
-   The temporal split has a large fraud-rate shift.
-   The final test set is small.
-   Zero false positives should not be generalized to production.
-   Review has no explicit analyst cost yet.
-   Probability calibration should be evaluated on a larger
    representative validation population.
-   Future work should include a larger held-out evaluation and
    independent/public validation where appropriate.
-   Scenario-level metrics should remain visible rather than relying
    only on aggregate performance.

------------------------------------------------------------------------

# 13. TESTING

``` powershell
python -m pytest tests\ -q
```

Final verified result:

``` text
49 passed
```

------------------------------------------------------------------------

# 14. FRONTEND BUILD

``` powershell
cd frontend
npm run build
```

Verified:

``` text
TypeScript compilation: PASS
Vite production build: PASS
```

------------------------------------------------------------------------

# 15. FIVE-MINUTE DEMO

``` text
Overview
  ↓
Evaluation
  ↓
Economics
  ↓
Transactions
  ↓
Transaction Detail
  ↓
AI Investigator
  ↓
49 passing tests
  ↓
Economics closing shot
```

Key message:

> **Detect with ML. Route with deterministic policy. Measure the
> economics. Explain with constrained AI. Never let the explanation
> layer override the risk engine.**

------------------------------------------------------------------------

# 16. SUBMISSION CHECKLIST

-   [ ] Public repository
-   [ ] README
-   [ ] Quick-start instructions
-   [ ] Complete folder structure
-   [ ] Architecture diagram
-   [ ] Five-minute pitch
-   [ ] Synthetic benchmark disclosed
-   [ ] Test-set limitations disclosed
-   [ ] False-positive cost disclosed
-   [ ] Review-cost limitation disclosed
-   [ ] Defense-only statement
-   [ ] No Gemini key committed
-   [ ] Backend works
-   [ ] Frontend works
-   [ ] Evaluation works
-   [ ] Economics works
-   [ ] Transactions works
-   [ ] Investigator works/falls back
-   [ ] 49 tests pass
-   [ ] Frontend build passes
-   [ ] Git working tree clean

------------------------------------------------------------------------

# 17. FINAL VERIFIED STATE

``` text
Backend tests:       49 passed
Frontend build:      PASS
TypeScript:          PASS
Economics page:      PASS
Economics chart:     PASS
Working tree:        CLEAN
Branch:              main
Final code commit:   bda0b02
```

> **Detect with ML. Route with deterministic policy. Measure the
> economics. Explain with constrained AI. Never let the explanation
> layer override the risk engine.**

------------------------------------------------------------------------

## License

Add the project's chosen license here if required.

## Acknowledgements

Built for the **Razorpay AI Buildathon 2026 --- Track 02: AI Risk
Manager**.
