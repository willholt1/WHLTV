from __future__ import annotations
from enum import IntEnum

# IDs mirror DB
class Side(IntEnum):
    T = 1
    CT = 2
    BOTH = 3

class VetoAction(IntEnum):
    PICK = 1
    BAN = 2
    REMAINING = 3

class Map(IntEnum):
    MIRAGE = 1
    INFERNO = 2
    NUKE = 3
    OVERPASS = 4
    VERTIGO = 5
    ANCIENT = 6
    ANUBIS = 7
    DUST2 = 8
    TRAIN = 9
    CACHE = 10
    COBBLESTONE = 11

MAP_NAME_TO_ENUM = {
    "mirage": Map.MIRAGE,
    "inferno": Map.INFERNO,
    "nuke": Map.NUKE,
    "overpass": Map.OVERPASS,
    "vertigo": Map.VERTIGO,
    "ancient": Map.ANCIENT,
    "anubis": Map.ANUBIS,
    "dust2": Map.DUST2,
    "train": Map.TRAIN,
    "cache": Map.CACHE,
    "cobblestone": Map.COBBLESTONE,
}

DE_MAP_NAME_TO_ENUM = {
    "de_mirage": Map.MIRAGE,
    "de_inferno": Map.INFERNO,
    "de_nuke": Map.NUKE,
    "de_overpass": Map.OVERPASS,
    "de_vertigo": Map.VERTIGO,
    "de_ancient": Map.ANCIENT,
    "de_anubis": Map.ANUBIS,
    "de_dust2": Map.DUST2,
    "de_train": Map.TRAIN,
    "de_cache": Map.CACHE,
    "de_cbble": Map.COBBLESTONE,
}

VETOACTION_TO_ENUM = {
    "picked": VetoAction.PICK,
    "removed": VetoAction.BAN,
    "was left over": VetoAction.REMAINING
}


def map_from_str(s: str) -> Map | None:
    return MAP_NAME_TO_ENUM.get(s.strip().lower())

def vetoaction_from_str(s: str) -> VetoAction:
    return VETOACTION_TO_ENUM.get(s.strip().lower())

def de_map_from_str(s: str) -> Map | None:
    return DE_MAP_NAME_TO_ENUM.get(s.strip().lower())