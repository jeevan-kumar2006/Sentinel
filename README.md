Sentinel — Phase 1: Final Data Foundation
Defensive AI merchant-risk system for the Razorpay AI Buildathon (Track 02).

Primary loss class: velocity and anomaly-based transaction fraud.

Phase 1 produces a realistic, reproducible, temporally correct, leakage-safesynthetic transaction dataset plus an independent point-in-time featureengineering pipeline. No model is trained. No UI is built. No database isused.

Important: the ~4% fraud prevalence used here is a syntheticbenchmark prevalence chosen to provide enough positive examples forhackathon evaluation. It is NOT a real-world or Razorpay fraud prevalence.

Architecture
1_generate_raw_events.py        ↓raw_events.csv          (immutable ground truth)        ↓2_engineer_features.py        ↓features.csv            (point-in-time derived features)
Raw events are never modified by feature engineering. Changing the velocitywindow from 5 → 10 minutes does NOT regenerate the raw dataset.

Files
sentinel/├── scripts/│   ├── 1_generate_raw_events.py│   └── 2_engineer_features.py├── data/generated/│   ├── raw_events.csv│   ├── raw_events_metadata.json│   ├── features.csv│   └── feature_metadata.json├── tests/│   ├── test_raw_generation.py│   └── test_temporal_features.py└── README.md
Quick start
python scripts/1_generate_raw_events.py \    --rows 50000 \    --seed 42 \    --fraud-rate 0.04python scripts/2_engineer_features.py \    --input data/generated/raw_events.csv \    --output data/generated/features.csv \    --velocity-window-minutes 5pytest tests/ -v
