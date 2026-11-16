"""Player-value model shared by the notebooks.

Same method as notebooks/draft_tool.ipynb: per-game stats blended from a base window and a recent window,
9-category z-scores against the draftable pool, and an injury adjustment from games played in recent seasons.
Downloads are cached in the project's data/ folder (shared with the draft tool).
"""
import re
import time
import unicodedata

import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, leaguegamelog, playercareerstats

CATS = ["FG_PCT", "FT_PCT", "FG3M", "PTS", "REB", "AST", "STL", "BLK", "TOV"]
LABELS = {"FG_PCT": "FG%", "FT_PCT": "FT%", "FG3M": "3PM", "PTS": "PTS", "REB": "REB",
          "AST": "AST", "STL": "STL", "BLK": "BLK", "TOV": "TO"}
PCT_CATS = {"FG_PCT": ("FGM", "FGA"), "FT_PCT": ("FTM", "FTA")}
BLEND = ["MIN", "PTS", "REB", "AST", "STL", "BLK", "FG3M", "TOV", "FGM", "FGA", "FTM", "FTA"]
POSITIONS = {"G": "Guard", "F": "Forward", "C": "Center"}

INK, INK_2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
POS, NEG, SURFACE = "#2a78d6", "#e34948", "#fcfcfb"


def norm(name):
    """Accent-, punctuation- and case-insensitive key for matching names across sources."""
    name = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return "".join(ch for ch in name.lower() if ch.isalnum())


def positions_of(position):
    """'F-C' -> ['F', 'C']"""
    return [p for p in str(position).split("-") if p in POSITIONS]


def cached(data, name, fetch, refresh=False):
    path = data / name
    if path.exists() and not refresh:
        return pd.read_csv(path)
    df = fetch()
    df.to_csv(path, index=False)
    time.sleep(0.6)  # be polite to NBA.com
    return df


def today():
    """Today's date in US Eastern time (the NBA's calendar), used to stamp daily cache files."""
    return f"{pd.Timestamp.now(tz='America/New_York'):%Y-%m-%d}"


def clean_daily_caches(data):
    """Delete date-stamped cache files from earlier days; returns how many were removed."""
    old = [f for f in data.glob("*.csv")
           if re.search(r"_\d{4}-\d{2}-\d{2}\.csv$", f.name) and not f.name.endswith(f"_{today()}.csv")]
    for f in old:
        f.unlink()
    return len(old)


def previous_season(season):
    """'2026-27' -> '2025-26'"""
    y = int(season[:4]) - 1
    return f"{y}-{str(y + 1)[2:]}"


def season_stats(data, season, in_progress=False):
    """Full-season per-game stats. A season in progress is re-downloaded once a day (date in the file name)."""
    tag = f"_{today()}" if in_progress else ""
    return cached(data, f"player_stats_{season}{tag}.csv", lambda: leaguedashplayerstats.LeagueDashPlayerStats(
        season=season, per_mode_detailed="PerGame", timeout=60).get_data_frames()[0])


WINDOW_UNITS = {"m": ("months", "month"), "w": ("weeks", "week"), "d": ("days", "day")}


def window_spec(window):
    """Normalize a window: 3 -> '3m' (months), '2w' (weeks), '14d' (days); None / 'all' -> None (whole season)."""
    if window in (None, 0, "all"):
        return None
    if isinstance(window, (int, float)):
        return f"{int(window)}m"
    window = str(window).strip().lower()
    assert window[:-1].isdigit() and window[-1] in WINDOW_UNITS, f"window must look like '2m', '2w' or '14d', not {window!r}"
    return window


def window_offset(window):
    """'2m' -> pd.DateOffset(months=2); None -> None."""
    spec = window_spec(window)
    return None if spec is None else pd.DateOffset(**{WINDOW_UNITS[spec[-1]][0]: int(spec[:-1])})


def window_label(window):
    spec = window_spec(window)
    n, unit = int(spec[:-1]), WINDOW_UNITS[spec[-1]][1]
    return f"{n} {unit}{'s' if n > 1 else ''}"


def season_span(data, season, in_progress=False):
    """(first game date, latest game date) of a season, or (None, None) before it starts."""
    tag = f"_{today()}" if in_progress else ""
    if season_stats(data, season, in_progress).empty:
        return None, None
    dates = cached(data, f"season_dates_{season}{tag}.csv", lambda: leaguegamelog.LeagueGameLog(
        season=season, timeout=60).get_data_frames()[0]["GAME_DATE"].agg(["min", "max"]).to_frame().T)
    return pd.Timestamp(dates["min"].iloc[0]), pd.Timestamp(dates["max"].iloc[0])


def season_window(data, season, months, in_progress=False):
    """Per-game stats for the last `months` of a season (a window like 3 / '2m' / '2w'; None = whole season),
    plus a label and the last game date."""
    tag = f"_{today()}" if in_progress else ""
    full = season_stats(data, season, in_progress)
    if full.empty:
        return full, f"{season} (no games yet)", None
    date_to = season_span(data, season, in_progress)[1]  # last game played so far
    spec = window_spec(months)
    if spec is None:
        return full.copy(), f"{season} season so far" if in_progress else f"full {season} season", date_to
    start = date_to - window_offset(spec)
    df = cached(data, f"player_stats_{season}_last{spec}{tag}.csv", lambda: leaguedashplayerstats.LeagueDashPlayerStats(
        season=season, per_mode_detailed="PerGame", date_from_nullable=start.strftime("%m/%d/%Y"),
        date_to_nullable=date_to.strftime("%m/%d/%Y"), timeout=60).get_data_frames()[0])
    return df, f"last {window_label(spec)} of {season}", date_to


def load_stats(data, season, base_months, recent_months, recent_weight, min_games, recent_min_games,
               in_progress=False, base_season=None, verbose=True):
    """Per-game stats blended (1 - recent_weight) x base window + recent_weight x recent window.

    The base window comes from `base_season` (default: `season`), so early in a season the base can be last
    season's final months while the recent window is this season's games. Returns (blended players, full-season
    stats of `season`, info). Raises ValueError if there's nothing to value."""
    base_season = base_season or season
    cross = base_season != season
    stats_full = season_stats(data, season, in_progress)
    if stats_full.empty and not cross:
        raise ValueError(f"No {season} regular-season games yet")

    # Base window; players with too few games in it fall back to that season's full-season stats
    base_full = season_stats(data, base_season, in_progress and not cross)
    base, base_label, base_to = season_window(data, base_season, base_months, in_progress and not cross)
    base = base[base["GP"] >= min_games]
    fallback = base_full[~base_full["PLAYER_ID"].isin(base["PLAYER_ID"])]
    if cross:
        # Only players with a real sample last season; rookies/returners get this season's games as their base
        fallback = fallback[fallback["GP"] >= min_games]
        stats = pd.concat([base, fallback], ignore_index=True)
        newcomers = stats_full[~stats_full["PLAYER_ID"].isin(stats["PLAYER_ID"]) & (stats_full["GP"] >= recent_min_games)]
        stats = pd.concat([stats, newcomers], ignore_index=True)
        stats["GP"] = stats["PLAYER_ID"].map(stats_full.set_index("PLAYER_ID")["GP"]).fillna(0).astype(int)
    else:
        stats = pd.concat([base, fallback], ignore_index=True)
        stats["GP"] = stats["PLAYER_ID"].map(stats_full.set_index("PLAYER_ID")["GP"])
    label = base_label
    date_to = base_to

    if recent_weight and not stats_full.empty:
        recent, recent_label, date_to = season_window(data, season, recent_months, in_progress)
        recent = recent[recent["GP"] >= recent_min_games]
        stats = stats.merge(recent[["PLAYER_ID", "GP", *BLEND]], on="PLAYER_ID", how="left", suffixes=("", "_R"))
        w = stats["GP_R"].notna() * recent_weight
        for c in BLEND:
            stats[c] = (1 - w) * stats[c] + w * stats[f"{c}_R"].fillna(0)
        for pct, (made, att) in PCT_CATS.items():
            stats[pct] = (stats[made] / stats[att].where(stats[att] > 0)).fillna(0)
        stats = stats.drop(columns=[c for c in stats if c.endswith("_R")])
        label = f"{1 - recent_weight:.0%} {base_label} + {recent_weight:.0%} {recent_label}"
    if verbose:
        print(f"Player values from: {label}" + (" (season in progress, refreshed daily)" if in_progress else ""))
    info = {"last_game": date_to, "source": label}
    if not cross:  # cross-season rows were already qualified above (GP here is this season's games)
        stats = stats[stats["GP"] >= min_games]
    stats = stats.reset_index(drop=True)
    if stats.empty:
        most = int(stats_full["GP"].max()) if len(stats_full) else 0
        raise ValueError(f"No {season} players have {min_games}+ games yet (most: {most}); "
                         f"lower the minimum games setting")
    return stats, stats_full, info


def zscores(df, pool_size, active):
    """Category z-scores against the draftable pool (FG%/FT% weighted by attempts, turnovers reversed)."""
    pool = df.nlargest(pool_size, "MIN")
    for _ in range(3):
        z = pd.DataFrame(index=df.index)
        for c in CATS:
            if c in PCT_CATS:
                made, att = PCT_CATS[c]
                league_pct = pool[made].sum() / pool[att].sum()
                impact = (df[c] - league_pct) * df[att]
                pool_impact = impact.loc[pool.index]
                z[c] = (impact - pool_impact.mean()) / pool_impact.std()
            else:
                z[c] = (df[c] - pool[c].mean()) / pool[c].std()
        z["TOV"] = -z["TOV"]
        z["TOTAL"] = z[active].sum(axis=1)
        pool = df.loc[z["TOTAL"].nlargest(pool_size).index]
    return z


def career_games(data, player_ids, verbose=True):
    """Games played per season for each player, cached in data/career_gp.csv (only missing players are fetched)."""
    path = data / "career_gp.csv"
    have = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["PLAYER_ID", "SEASON_ID", "GP"])
    todo = [p for p in player_ids if p not in set(have["PLAYER_ID"])]
    if todo and verbose:
        print(f"Downloading games-played history for {len(todo)} players...")
    rows = []
    for i, pid in enumerate(todo, 1):
        for _ in range(3):
            try:
                df = playercareerstats.PlayerCareerStats(player_id=pid, timeout=60).get_data_frames()[0]
                break
            except Exception:
                time.sleep(3)
        else:
            continue
        gp = df.groupby("SEASON_ID", as_index=False)["GP"].max()  # traded players: the 'TOT' row is the max
        gp["PLAYER_ID"] = pid
        rows.append(gp[["PLAYER_ID", "SEASON_ID", "GP"]])
        time.sleep(0.6)
        if i % 25 == 0 or i == len(todo):
            have = pd.concat([have, *rows], ignore_index=True)
            rows = []
            have.to_csv(path, index=False)
    return have[have["PLAYER_ID"].isin(player_ids)]


def availability(gp_hist, hist_seasons, season_weights, shrink=1.0, season_games=None):
    """Share of games available, weighted toward recent seasons and shrunk toward the league average.
    season_games gives the games played so far in a season in progress (default 82); that season's
    weight is scaled by how much of it has been played."""
    season_games = season_games or {}
    raw = {}
    for pid, g in gp_hist.groupby("PLAYER_ID"):
        by_season = dict(zip(g["SEASON_ID"], g["GP"]))
        seasons = [(s, w * season_games.get(s, 82) / 82, season_games.get(s, 82))
                   for s, w in zip(hist_seasons, season_weights) if s >= g["SEASON_ID"].min()]
        seasons = [(s, w, n) for s, w, n in seasons if w > 0]
        if seasons:
            rate = sum(w * min(by_season.get(s, 0), n) / n for s, w, n in seasons) / sum(w for _, w, _ in seasons)
            raw[pid] = (rate, len(seasons))
    league_avg = pd.Series([r for r, _ in raw.values()]).mean()
    return {pid: (n * r + shrink * league_avg) / (n + shrink) for pid, (r, n) in raw.items()}, league_avg


def player_values(data, season="2025-26", num_teams=14, roster_size=10, base_months=3, recent_months=1,
                  recent_weight=0.3, min_games=10, recent_min_games=6, injury_weight=1.0,
                  season_weights=(0.7, 0.3), punt=(), in_progress=False, base_season=None, verbose=True):
    """One row per player: category z-scores, TOTAL, AVAIL and injury-adjusted ADJ_TOTAL (draft-tool method).
    in_progress=True for the current season: stats refresh daily and availability counts games so far."""
    players, stats_full, info = load_stats(data, season, base_months, recent_months, recent_weight, min_games,
                                     recent_min_games, in_progress, base_season, verbose)
    active = [c for c in CATS if c not in punt]
    pool_size = num_teams * roster_size
    z = zscores(players, pool_size, active)
    values = pd.concat([players[["PLAYER_ID", "PLAYER_NAME", "GP", "MIN"]], z], axis=1)

    start = int(season[:4])
    hist_seasons = [f"{y}-{str(y + 1)[2:]}" for y in range(start, start - len(season_weights), -1)]
    top_ids = values.nlargest(pool_size + 75, "TOTAL")["PLAYER_ID"].tolist()
    gp_hist = career_games(data, top_ids, verbose)
    season_games = {}
    if in_progress and not stats_full.empty:
        # The career cache is never refreshed, so take this season's games from today's stats instead
        current = stats_full.loc[stats_full["PLAYER_ID"].isin(top_ids), ["PLAYER_ID", "GP"]].assign(SEASON_ID=season)
        gp_hist = pd.concat([gp_hist[gp_hist["SEASON_ID"] != season], current], ignore_index=True)
        season_games = {season: max(1, int(stats_full["GP"].max()))}  # ~games each team has played so far
    avail, league_avg = availability(gp_hist, hist_seasons, season_weights, season_games=season_games)
    values["AVAIL"] = values["PLAYER_ID"].map(avail).fillna(league_avg).round(2)
    replacement = values["TOTAL"].nlargest(pool_size).min()
    adjusted = values["AVAIL"] * values["TOTAL"] + (1 - values["AVAIL"]) * replacement
    values["ADJ_TOTAL"] = injury_weight * adjusted + (1 - injury_weight) * values["TOTAL"]
    values = values.sort_values("ADJ_TOTAL", ascending=False).reset_index(drop=True)
    values.attrs.update(info)  # last_game: latest game in the stats; source: which windows were blended
    return values


KEY_TO_CAT = {**{c.lower(): c for c in CATS}, **{label.lower(): c for c, label in LABELS.items()}}


def parse_weights(weights, punt=()):
    """{"3PM": -0.4, "STL": 0.2, "TO": 0.2} -> per-category multipliers {"FG3M": 0.6, "STL": 1.2, ...}.
    Same rules as the draft tool: adjustments are added to 1.0 and must sum to 0; punted categories get 0."""
    weights = weights or {}
    unknown = [k for k in weights if k.lower() not in KEY_TO_CAT]
    if unknown:
        raise ValueError(f"Unknown categories {unknown}. Use one of {list(LABELS.values())}")
    deltas = {KEY_TO_CAT[k.lower()]: v for k, v in weights.items()}
    punted = [LABELS[c] for c in deltas if c in punt]
    if punted:
        raise ValueError(f"{punted} are punted (weight 0); remove them from weights or from punt")
    total = sum(deltas.values())
    if abs(total) > 1e-6:
        raise ValueError(f"Weights must sum to 0 to conserve total weight; yours sum to {total:+.2f}")
    mult = {c: 0.0 if c in punt else 1 + deltas.get(c, 0) for c in CATS}
    negative = [LABELS[c] for c, m in mult.items() if m < 0]
    if negative:
        raise ValueError(f"{negative} would get a negative weight (adjustment below -1)")
    return mult


def draw_profile(ax, z_tot, order, title, span, before=None, fontsize=9, punt=()):
    """Diverging bars of summed z-scores per category; optional tick marks show a 'before' profile."""
    ax.set_facecolor(SURFACE)
    colors = [BASE if c in punt else POS if z_tot[c] >= 0 else NEG for c in order]
    ax.barh([LABELS[c] for c in order], z_tot[order], color=colors, height=0.6)
    if before is not None:
        ax.scatter(before[order], range(len(order)), marker="|", s=140, linewidths=1.6, color=INK, zorder=3)
    for y, c in enumerate(order):
        v = z_tot[c]
        edge = v if before is None else (max(v, before[c], 0) if v >= 0 else min(v, before[c], 0))
        ax.text(edge + (0.04 if v >= 0 else -0.04) * span, y, f"{v:+.1f}", va="center",
                ha="left" if v >= 0 else "right", fontsize=fontsize - 1, color=INK_2)
    ax.axvline(0, color=BASE, linewidth=1)
    ax.set_xlim(-span * 1.25, span * 1.25)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=MUTED, length=0, labelsize=fontsize)
    for label in ax.get_yticklabels():
        label.set_color(INK)
    ax.set_title(title, loc="left", color=INK, fontsize=fontsize + 1)
