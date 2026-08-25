import json
import pandas as pd
from pathlib import Path
from datetime import timedelta
from typing import Tuple, Dict

ROOT = Path(__file__).resolve().parents[2]
FEATURES_PATH = ROOT / "data" / "generated" / "features.csv"
META_PATH = ROOT / "data" / "generated" / "raw_events_metadata.json"

def load_data() -> Tuple[pd.DataFrame, Dict]:
    df = pd.read_csv(FEATURES_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    with open(META_PATH, 'r') as f:
        meta = json.load(f)
    
    attack_start = pd.to_datetime(meta['timeline']['attack_start'])
    attack_end = pd.to_datetime(meta['timeline']['attack_end'])
    attack_duration = attack_end - attack_start
    
    train_attack_end = attack_start + timedelta(seconds=0.60 * attack_duration.total_seconds())
    val_end = attack_start + timedelta(seconds=0.80 * attack_duration.total_seconds())
    
    train_df = df[df['timestamp'] < train_attack_end].copy()
    val_df = df[(df['timestamp'] >= train_attack_end) & (df['timestamp'] < val_end)].copy()
    test_df = df[df['timestamp'] >= val_end].copy()
    
    splits = {
        'train': train_df,
        'validation': val_df,
        'test': test_df
    }
    
    # Fail loudly if split is invalid
    for name, split in splits.items():
        if not (0 in split['is_fraud'].values and 1 in split['is_fraud'].values):
            raise ValueError(f"Temporal split '{name}' does not contain both classes.")
            
    boundaries = {
        'attack_start': attack_start,
        'attack_end': attack_end,
        'train_attack_end': train_attack_end,
        'validation_end': val_end
    }
    
    return splits, boundaries