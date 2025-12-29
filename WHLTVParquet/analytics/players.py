# hltvparquet/analytics/players.py

from __future__ import annotations
from typing import Tuple

import pandas as pd

from ..map import HLTVMap
from .. import schema_helpers as sh
from . import kills as kills_mod


def adr(
    map: HLTVMap,
    *,
    exclude_team_damage: bool = False,
    exclude_self_damage: bool = True,
) -> pd.Series:
    """
    Average Damage per Round (ADR).

    - Only counts damage within validated round intervals
    - Optionally excludes team damage
    - Optionally excludes self damage
    """

    # -----------------------
    # Preconditions
    # -----------------------
    rounds = map.rounds
    if rounds.empty:
        return pd.Series(dtype="float")

    ev = map.events
    if ev.empty:
        return pd.Series(dtype="float")

    # -----------------------
    # Select damage events
    # -----------------------
    dmg = ev[ev[sh.EVENT_TYPE_COL] == sh.EVENT_PLAYER_HURT].copy()
    if dmg.empty:
        return pd.Series(dtype="float")

    sh.ensure_columns(dmg, [sh.TICK_COL, "dmg_health"], "ADR")

    # -----------------------
    # Filter to events inside valid rounds
    # -----------------------
    # Build array of (start, end) intervals
    intervals = rounds[["start_tick", "end_tick"]].to_numpy()

    # Vectorised interval check
    ticks = dmg[sh.TICK_COL].to_numpy()

    in_round = pd.Series(False, index=dmg.index)

    for start, end in intervals:
        in_round |= (ticks >= start) & (ticks <= end)

    dmg = dmg[in_round]

    if dmg.empty:
        return pd.Series(dtype="float")

    # -----------------------
    # Identify attacker / victim
    # -----------------------
    attacker_col = next(
        (c for c in ["attacker_steamid", "attacker"] if c in dmg.columns),
        None
    )
    victim_col = next(
        (c for c in ["user_steamid", "victim_steamid", "userid"] if c in dmg.columns),
        None
    )

    if attacker_col is None or victim_col is None:
        raise ValueError("ADR: attacker or victim column not found")

    # -----------------------
    # Exclude self damage
    # -----------------------
    if exclude_self_damage:
        dmg = dmg[dmg[attacker_col] != dmg[victim_col]]

    # -----------------------
    # Exclude team damage
    # -----------------------
    if exclude_team_damage:
        attacker_team_col = next(
            (c for c in ["attacker_team", "attacker_team_num"] if c in dmg.columns),
            None
        )
        victim_team_col = next(
            (c for c in ["user_team", "team_num"] if c in dmg.columns),
            None
        )

        if attacker_team_col and victim_team_col:
            dmg = dmg[dmg[attacker_team_col] != dmg[victim_team_col]]

    if dmg.empty:
        return pd.Series(dtype="float")

    # -----------------------
    # Aggregate damage
    # -----------------------
    total_damage = dmg.groupby(attacker_col)["dmg_health"].sum()

    # -----------------------
    # Divide by valid round count
    # -----------------------
    n_rounds = len(rounds)

    return (total_damage / n_rounds).sort_values(ascending=False)


def kpr(map: HLTVMap) -> pd.Series:
    """
    Kills per round (KPR) per attacking player.

    Requires:
    - event_type == 'player_death'
    - 'attacker_steamid'
    """
    kills = kills_mod.kills_per_player(map)
    n_rounds = len(map.rounds)

    return (kills / n_rounds).sort_values(ascending=False)

def basic_player_stats(map: HLTVMap) -> pd.DataFrame:
    """
    Basic per-player stats: kills, deaths, ADR.
    KAST, rating etc can be added later.

    Output index/column:
    - steamid
    - kills
    - deaths
    - adr
    - kd_diff
    - kpr (kills per round)
    """
    df_ticks = map.ticks
    if df_ticks.empty:
        return pd.DataFrame(columns=["steamid", "kills", "deaths", "adr", "kd_diff", "kpr"])

    # steamid column to use for core identity
    steamid_col = sh.PLAYER_STEAMID_COL if sh.PLAYER_STEAMID_COL in df_ticks.columns else "steamid"
    sh.ensure_columns(df_ticks, [steamid_col], "basic_player_stats (ticks)")

    # kills per attacker
    k = kills_mod.kills_per_player(map)
    k.name = "kills"

    # deaths per victim
    ev = map.events
    deaths = ev[ev[sh.EVENT_TYPE_COL] == sh.EVENT_PLAYER_DEATH].copy()
    victim_col = None
    for cand in ["user_steamid", "victim_steamid", "userid"]:
        if cand in deaths.columns:
            victim_col = cand
            break
    if victim_col is None:
        # we can still emit kill-only stats
        victim_counts = pd.Series(dtype="int64", name="deaths")
    else:
        victim_counts = deaths.groupby(victim_col).size()
        victim_counts.name = "deaths"

    # ADR
    adr_series = adr(map)
    adr_series.name = "adr"

    # KPR
    kpr_series = kpr(map)
    kpr_series.name = "kpr"

    # union of all player ids present in any stat
    idx = sorted(
        set(k.index.tolist())
        .union(victim_counts.index.tolist())
        .union(adr_series.index.tolist())
    )

    stats = pd.DataFrame(index=idx)
    stats.index.name = "steamid"
    stats["kills"] = k.reindex(stats.index).fillna(0).astype(int)
    stats["deaths"] = victim_counts.reindex(stats.index).fillna(0).astype(int)
    stats["adr"] = adr_series.reindex(stats.index).fillna(0.0)
    stats["kd_diff"] = stats["kills"] - stats["deaths"]
    stats["kpr"] = kpr_series.reindex(stats.index).fillna(0.0)

    return stats.sort_values(["kills", "adr"], ascending=[False, False])
