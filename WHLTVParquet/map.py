# hltvparquet/map.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

import pandas as pd

from . import schema_helpers as sh


@dataclass
class HLTVMap:
    """
    Wrapper around a single parquet file produced by your demoToParquet pipeline.

    Assumptions:
    - All data (ticks + events + non-player events) is in a single table.
    - event rows have a non-null 'event_type' column.
    - pure tick rows (per-player state) have a non-null 'player_steamid'.
    """

    path: str
    df: pd.DataFrame

    @classmethod
    def from_parquet(cls, path: str) -> "HLTVMap":
        df = pd.read_parquet(path)
        return cls(path=path, df=df)

    def __init__(self, path: str):
        self.path = path
        self.df = pd.read_parquet(path)

        # basic slices
        self._event_df: Optional[pd.DataFrame] = None
        self._tick_df: Optional[pd.DataFrame] = None
        self._round_df: Optional[pd.DataFrame] = None

    # -----------------------
    # Core slices
    # -----------------------
    @property
    def events(self) -> pd.DataFrame:
        if self._event_df is None:
            if sh.EVENT_TYPE_COL in self.df.columns:
                self._event_df = self.df[self.df[sh.EVENT_TYPE_COL].notna()].copy()
            else:
                self._event_df = self.df.iloc[0:0].copy()  # empty
        return self._event_df

    @property
    def ticks(self) -> pd.DataFrame:
        """
        Per-player tick rows (player state). We treat any row with a non-null
        player_steamid as a "tick row".
        """
        if self._tick_df is None:
            if sh.PLAYER_STEAMID_COL in self.df.columns:
                self._tick_df = self.df[self.df[sh.PLAYER_STEAMID_COL].notna()].copy()
            else:
                self._tick_df = self.df.iloc[0:0].copy()
        return self._tick_df

    # -----------------------
    # Metadata helpers
    # -----------------------
    def players(self) -> List[str]:
        if sh.PLAYER_STEAMID_COL not in self.df.columns:
            return []
        return sorted(self.df[sh.PLAYER_STEAMID_COL].dropna().unique().tolist())

    def player_names(self) -> pd.DataFrame:
        """
        Returns a mapping of steamid -> list of names used across the map.
        """
        sh.ensure_columns(self.df, [sh.PLAYER_STEAMID_COL, sh.PLAYER_NAME_COL], "player_names")
        grouped = self.df.groupby(sh.PLAYER_STEAMID_COL)[sh.PLAYER_NAME_COL] \
                         .agg(lambda s: sorted({n for n in s.dropna()})) \
                         .reset_index()
        return grouped

    def teams(self) -> Optional[pd.DataFrame]:
        """
        Returns team_num -> team_name + team_clan_name if columns exist.
        """
        cols = [c for c in ["team_num", "team_name", "team_clan_name"] if c in self.df.columns]
        if not cols:
            return None
        team_df = self.df[cols].dropna(subset=["team_num"]).drop_duplicates("team_num")
        return team_df.sort_values("team_num")

    # -----------------------
    # Round information
    # -----------------------
    @property
    def rounds(self) -> pd.DataFrame:
        """
        Build a basic rounds table from round_start / round_end events.

        Columns (when available):
        - round_number
        - start_tick
        - end_tick
        - reason (from 'reason' or 'round_win_reason')
        - round_win_status (if present)
        """
        if self._round_df is not None:
            return self._round_df

        ev = self.events
        if ev.empty:
            self._round_df = ev.iloc[0:0].copy()
            return self._round_df

        # round_start & round_end events
        rs = ev[ev[sh.EVENT_TYPE_COL] == sh.EVENT_ROUND_START].copy()
        re = ev[ev[sh.EVENT_TYPE_COL] == sh.EVENT_ROUND_END].copy()

        if rs.empty and re.empty:
            self._round_df = ev.iloc[0:0].copy()
            return self._round_df

        # if no explicit start events, infer from round_end ticks
        if rs.empty and not re.empty:
            rs = re[[sh.TICK_COL]].copy()
            rs[sh.EVENT_TYPE_COL] = sh.EVENT_ROUND_START

        rs = rs.sort_values(sh.TICK_COL).reset_index(drop=True)
        re = re.sort_values(sh.TICK_COL).reset_index(drop=True)

        rs["round_number"] = rs.index + 1
        # align ends by index; if fewer ends than starts, forward-fill
        re["round_number"] = re.index + 1
        re = re.set_index("round_number")

        round_rows = []
        for _, start_row in rs.iterrows():
            rno = start_row["round_number"]
            start_tick = start_row.get(sh.TICK_COL, None)

            end_row = re.loc[rno] if rno in re.index else None
            end_tick = end_row[sh.TICK_COL] if end_row is not None else None

            reason = None
            round_win_status = None

            # prefer 'reason' if present (you forced it to string in your pipeline)
            if end_row is not None:
                if "reason" in end_row.index:
                    reason = end_row["reason"]
                elif "round_win_reason" in end_row.index:
                    reason = end_row["round_win_reason"]

                if "round_win_status" in end_row.index:
                    round_win_status = end_row["round_win_status"]

            round_rows.append(
                {
                    "round_number": rno,
                    "start_tick": start_tick,
                    "end_tick": end_tick,
                    "reason": reason,
                    "round_win_status": round_win_status,
                }
            )

        self._round_df = pd.DataFrame(round_rows)
        return self._round_df

    # -----------------------
    # Delegates into analytics
    # -----------------------
    def basic_player_stats(self) -> pd.DataFrame:
        from .analytics import players as a_players
        return a_players.basic_player_stats(self)

    def kill_events(self) -> pd.DataFrame:
        from .analytics import kills as a_kills
        return a_kills.get_kill_events(self)

    def adr(self) -> pd.Series:
        from .analytics import players as a_players
        return a_players.adr(self)

    def economy_timeline(self) -> pd.DataFrame:
        from .analytics import economy as a_eco
        return a_eco.economy_timeline(self)

    def positions(self, steamid: str) -> pd.DataFrame:
        from .analytics import positions as a_pos
        return a_pos.player_positions(self, steamid)
