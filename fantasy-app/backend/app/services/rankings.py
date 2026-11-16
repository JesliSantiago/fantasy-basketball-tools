"""Thin wrapper around fantasy_core.player_values with an in-memory cache."""
from functools import lru_cache

from app import config  # noqa: F401  (sets up sys.path for fantasy_core)
import fantasy_core as fc


@lru_cache(maxsize=16)
def _values(season, num_teams, roster_size, punt):
    return fc.player_values(config.DATA_DIR, season=season, num_teams=num_teams,
                            roster_size=roster_size, punt=punt, verbose=False)


def rankings(season, num_teams, roster_size, punt, limit):
    df = _values(season, num_teams, roster_size, punt).head(limit).round(3)
    df = df.astype(object).where(df.notna(), None)  # NaN -> null for JSON
    return {
        "season": season,
        "categories": [{"key": c, "label": fc.LABELS[c]} for c in fc.CATS],
        "meta": {k: str(v) for k, v in df.attrs.items()},
        "players": df.to_dict(orient="records"),
    }
