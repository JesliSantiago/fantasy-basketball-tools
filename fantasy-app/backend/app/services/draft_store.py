"""Read/write data/draft_picks.json, the same file the notebooks use."""
import json

from app import config

DRAFT_FILE = config.DATA_DIR / "draft_picks.json"
EMPTY = {"taken": [], "mine": [], "history": []}


def load():
    if not DRAFT_FILE.exists():
        return dict(EMPTY)
    return {**EMPTY, **json.loads(DRAFT_FILE.read_text(encoding="utf-8"))}


def save(picks):
    DRAFT_FILE.write_text(json.dumps(picks, ensure_ascii=False, indent=1), encoding="utf-8")
