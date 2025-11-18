from dataclasses import dataclass, field, asdict, is_dataclass
from enum import IntEnum
from typing import Optional, Any, List
from datetime import datetime
from .enums import Map, Side, VetoAction

@dataclass
class StatLine:
    mapID: Map   
    sideID: Side
    kills: int
    deaths: int
    ADR: float
    swingPct: Optional[float] = None
    HLTVRating: float = 0.0
    HLTVRatingVersion: str = "3.0"

@dataclass
class Player:
    alias: str
    team: Optional[str] = None
    stats: List[StatLine] = field(default_factory=list)

@dataclass
class Veto:
    stepNumber: int
    teamName: str
    vetoActionID: VetoAction
    mapID: Map

@dataclass
class MatchData:
    matchID: int
    matchDate: datetime
    matchNotes: Optional[str] = None
    demoLink: Optional[str] = None
    matchVeto: List[Veto] = field(default_factory=list)
    players: List[Player] = field(default_factory=list)