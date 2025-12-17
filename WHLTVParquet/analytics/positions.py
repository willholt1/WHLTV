# hltvparquet/analytics/positions.py

from __future__ import annotations
import pandas as pd

from ..map import HLTVMap
from .. import schema_helpers as sh


def player_positions(map: HLTVMap, steamid: str) -> pd.DataFrame:
    """
    Tick-level positions for one player: (tick, X, Y, Z).

    You can feed this into heatmap plotting or path visualisations.
    """
    ticks = map.ticks
    sh.ensure_columns(ticks, [sh.TICK_COL, sh.PLAYER_STEAMID_COL, "X", "Y", "Z"], "player_positions")

    df = ticks[ticks[sh.PLAYER_STEAMID_COL] == steamid][[sh.TICK_COL, "X", "Y", "Z"]].copy()
    return df.sort_values(sh.TICK_COL)
