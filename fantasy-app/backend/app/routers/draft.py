from fastapi import APIRouter

from app.services import draft_store

router = APIRouter(tags=["draft"])


@router.get("/draft")
def get_draft():
    """Current picks from data/draft_picks.json (shared with the notebooks)."""
    return draft_store.load()
