# hltvparquet/analytics/kills.py

from __future__ import annotations
import pandas as pd

from ..map import HLTVMap
from .. import schema_helpers as sh


def get_kill_events(map: HLTVMap) -> pd.DataFrame:
    """
    Return kill events (player_death rows).
    Handles common attacker/victim column patterns from demoparser2.

    NOTE: Depending on how demoparser2 names fields, you may want to tweak
    column names here (attacker_steamid, attacker, userid, etc.).
    """
    ev = map.events
    if ev.empty:
        return ev

    kills = ev[ev[sh.EVENT_TYPE_COL] == sh.EVENT_PLAYER_DEATH].copy()
    return kills


def kills_per_player(map: HLTVMap) -> pd.Series:
    """
    Count kills per attacker_steamid where that column exists,
    otherwise fall back to attacker or similar.
    """
    kills = get_kill_events(map)
    if kills.empty:
        return pd.Series(dtype="int64")

    # choose best attacker column
    attacker_col = None
    for candidate in ["attacker_steamid", "attacker", "user_steamid"]:
        if candidate in kills.columns:
            attacker_col = candidate
            break

    if attacker_col is None:
        raise ValueError("No attacker column found in kill events; adjust kills_per_player().")

    return kills.groupby(attacker_col).size().sort_values(ascending=False)
