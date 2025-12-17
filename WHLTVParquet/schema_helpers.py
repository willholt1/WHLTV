# hltvparquet/schema_helpers.py

from typing import Iterable, Set

# Core columns your pipeline definitely has
TICK_COL = "tick"
EVENT_TYPE_COL = "event_type"
PLAYER_STEAMID_COL = "player_steamid"
PLAYER_NAME_COL = "player_name"

# Common event_type values
EVENT_PLAYER_DEATH = "player_death"
EVENT_PLAYER_HURT = "player_hurt"
EVENT_BOMB_PLANTED = "bomb_planted"
EVENT_BOMB_EXPLODED = "bomb_exploded"
EVENT_ROUND_START = "round_start"
EVENT_ROUND_END = "round_end"
EVENT_FLASH_DETONATE = "flashbang_detonate"
EVENT_HE_DETONATE = "hegrenade_detonate"
EVENT_INFERNO_START = "inferno_startburn"

def ensure_columns(df, required: Iterable[str], context: str = ""):
    """
    Raise a clear error if required columns are missing. This keeps analytics
    functions honest when your schema evolves.
    """
    cols: Set[str] = set(df.columns)
    missing = [c for c in required if c not in cols]
    if missing:
        raise ValueError(
            f"Missing columns for {context or 'operation'}: {missing}. "
            f"Available columns: {sorted(cols)}"
        )
