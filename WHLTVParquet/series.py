# hltvparquet/series.py
from __future__ import annotations
from typing import List

import pandas as pd
from .map import HLTVMap


class HLTVSeries:
    def __init__(self, maps: List[HLTVMap]):
        self.maps = maps

    def players(self):
        players = set()
        for m in self.maps:
            players.update(m.players())
        return sorted(players)

    def adr(self):
        """
        Series-level ADR = sum(damage across maps) / total rounds played
        """
        dfs = []
        total_rounds = 0

        for m in self.maps:
            adr_map = m.adr()
            rounds = len(m.rounds)
            total_rounds += rounds
            dfs.append((adr_map * rounds).rename("weighted_adr"))

        if not dfs or total_rounds == 0:
            return pd.Series(dtype="float")

        combined = pd.concat(dfs, axis=1).fillna(0)
        return combined.sum(axis=1) / total_rounds

    def maps_won(self):
        results = []
        for m in self.maps:
            r = m.rounds
            if r.empty:
                continue
            results.append(r["round_win_status"].iloc[-1])
        return results
