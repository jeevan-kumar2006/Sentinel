import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parents[1] / "backend" / "ml"))

from evaluation import run_phase2

if __name__ == "__main__":
    run_phase2()