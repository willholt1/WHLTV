# hltvparquet/loaders.py
from .map import HLTVMap

def load_map(parquet_path: str) -> HLTVMap:
    """
    Convenience loader for a single parquet map file.
    """
    return HLTVMap(parquet_path)
