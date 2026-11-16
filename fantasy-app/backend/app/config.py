"""Paths and settings. The app reuses fantasy-tools/src/fantasy_core.py and its data/ cache."""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = Path(os.getenv("FANTASY_TOOLS_DIR", REPO_ROOT / "fantasy-tools"))
DATA_DIR = Path(os.getenv("FANTASY_DATA_DIR", TOOLS_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Make `import fantasy_core` work without packaging it
_src = str(TOOLS_DIR / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

# Vite dev server origins allowed to call the API
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

# League defaults (mirror the notebooks' Settings cells)
DEFAULT_SEASON = os.getenv("FANTASY_SEASON", "2025-26")
NUM_TEAMS = int(os.getenv("FANTASY_NUM_TEAMS", "14"))
ROSTER_SIZE = int(os.getenv("FANTASY_ROSTER_SIZE", "10"))
