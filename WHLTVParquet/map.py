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
        if self._round_df is not None:
            return self._round_df

        ev = self.events
        if ev.empty:
            self._round_df = pd.DataFrame(
                columns=["round_number", "start_tick", "end_tick"]
            )
            return self._round_df

        # ---------------------------------
        # Build lifecycle event stream
        # ---------------------------------
        round_events = ev[
            ev[sh.EVENT_TYPE_COL].isin([
                "round_start",
                "round_freeze_end",
                "round_end",
                "round_officially_ended",
            ])
        ].copy()

        round_events = round_events.sort_values(sh.TICK_COL).reset_index(drop=True)

        # ---------------------------------
        # Sequential scan (ORDERED, NOT ADJACENT)
        # ---------------------------------
        rounds = []
        i = 0

        # ---------------------------------
        # Edge case: missing round_start at beginning
        # ---------------------------------
        if not round_events.empty:
            first_evt = round_events.loc[0, sh.EVENT_TYPE_COL]
            if first_evt in ("round_freeze_end", "round_end", "round_officially_ended"):
                synthetic_start = {
                    sh.EVENT_TYPE_COL: "round_start",
                    sh.TICK_COL: round_events.loc[0, sh.TICK_COL] - 1
                }
                round_events = pd.concat(
                    [pd.DataFrame([synthetic_start]), round_events],
                    ignore_index=True
                )


        rounds = []
        i = 0
        
        while i < len(round_events):
            evt = round_events.loc[i]
        
            if evt[sh.EVENT_TYPE_COL] != "round_start":
                i += 1
                continue
            
            start_tick = evt[sh.TICK_COL]
            j = i + 1
            end_idx = None
        
            while j < len(round_events):
                etype = round_events.loc[j, sh.EVENT_TYPE_COL]
        
                if etype in ("round_end", "round_officially_ended"):
                    end_idx = j
                    break
                
                if etype == "round_start":
                    # restart — abandon this start
                    break
                
                j += 1
        
            if end_idx is None:
                i += 1
                continue
            
            end_tick = round_events.loc[end_idx, sh.TICK_COL]
        
            rounds.append({
                "round_number": len(rounds) + 1,
                "start_tick": start_tick,
                "end_tick": end_tick,
            })
        
            i = end_idx + 1
        
    
    
        self._round_df = pd.DataFrame(rounds)
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
