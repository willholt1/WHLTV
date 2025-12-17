# hltvparquet/analytics/utility.py

from __future__ import annotations
import pandas as pd

from ..map import HLTVMap
from .. import schema_helpers as sh


def flash_events(map: HLTVMap) -> pd.DataFrame:
    """
    Returns flashbang detonation events.
    """
    ev = map.events
    return ev[ev[sh.EVENT_TYPE_COL] == sh.EVENT_FLASH_DETONATE].copy()


def he_events(map: HLTVMap) -> pd.DataFrame:
    """
    Returns HE grenade detonation events.
    """
    ev = map.events
    return ev[ev[sh.EVENT_TYPE_COL] == sh.EVENT_HE_DETONATE].copy()


def inferno_events(map: HLTVMap) -> pd.DataFrame:
    """
    Returns inferno (molotov/incendiary) start events.
    """
    ev = map.events
    return ev[ev[sh.EVENT_TYPE_COL] == sh.EVENT_INFERNO_START].copy()
