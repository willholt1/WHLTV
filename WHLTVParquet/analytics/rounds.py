# hltvparquet/analytics/rounds.py

from __future__ import annotations
import pandas as pd

from ..map import HLTVMap
from .. import schema_helpers as sh


def rounds_table(map: HLTVMap) -> pd.DataFrame:
    """
    Thin wrapper around map.rounds for consistency in analytics namespace.
    """
    return map.rounds.copy()
