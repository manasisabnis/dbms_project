"""Shared paths for the Legal Case Citation Analyzer ETL."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(
    os.getenv("LEGAL_DATA_DIR", str(REPO_ROOT / "data"))
).expanduser().resolve()
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = REPO_ROOT

def require_file(path: Path) -> Path:
    """Return an existing input path or raise a useful error."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Required ETL input not found: {path}\n"
            "Set LEGAL_DATA_DIR to the directory containing processed/."
        )
    return path
