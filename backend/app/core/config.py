from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

ARTIFACTS_DIR = ROOT / "artifacts"
DATA_DIR = ROOT / "data" / "generated"
REPORTS_DIR = ROOT / "reports"

FEATURES_PATH = DATA_DIR / "features.csv"
RAW_EVENTS_PATH = DATA_DIR / "raw_events.csv"

MODEL_PATH = ARTIFACTS_DIR / "selected_model.joblib"
PREPROCESSOR_PATH = ARTIFACTS_DIR / "preprocessing.joblib"
THRESHOLD_CONFIG_PATH = ARTIFACTS_DIR / "threshold_config.json"
SELECTED_FEATURES_PATH = ARTIFACTS_DIR / "selected_features.json"

EVALUATION_REPORT_PATH = REPORTS_DIR / "phase2_evaluation.json"