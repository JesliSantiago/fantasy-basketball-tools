from fastapi import APIRouter, Query

from app import config
from app.services import rankings as svc

router = APIRouter(tags=["rankings"])


@router.get("/rankings")
def get_rankings(
    season: str = config.DEFAULT_SEASON,
    num_teams: int = config.NUM_TEAMS,
    roster_size: int = config.ROSTER_SIZE,
    punt: list[str] = Query(default=[]),
    limit: int = 200,
):
    """9-category z-score rankings (draft-tool method). The first call per season downloads from NBA.com."""
    return svc.rankings(season, num_teams, roster_size, tuple(sorted(punt)), limit)
