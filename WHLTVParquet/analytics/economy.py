# hltvparquet/analytics/economy.py

from __future__ import annotations
import pandas as pd

from ..map import HLTVMap
from .. import schema_helpers as sh


def economy_timeline(map: HLTVMap) -> pd.DataFrame:
    """
    Returns tick-level economy state (money + equipment value per player).

    Requires tick columns:
    - 'balance'          (current money)
    - 'round_start_equip_value' (optional)
    - 'current_equip_value'     (optional)
    """
    ticks = map.ticks
    if ticks.empty:
        return ticks

    cols = [sh.TICK_COL, sh.PLAYER_STEAMID_COL]
    optional_cols = ["balance", "round_start_equip_value", "current_equip_value"]
    present_optionals = [c for c in optional_cols if c in ticks.columns]

    sh.ensure_columns(ticks, cols, "economy_timeline")

    eco = ticks[cols + present_optionals].copy()
    eco = eco.sort_values([sh.TICK_COL, sh.PLAYER_STEAMID_COL])
    return eco
