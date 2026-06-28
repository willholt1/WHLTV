from importlib import import_module

__all__ = [
    "generate_scoreboard",
    "generate_map_surface",
    "draw_map_surface",
]


def __getattr__(name):
    if name == "generate_scoreboard":
        return import_module(".extractStats", __name__).generate_scoreboard
    if name == "generate_map_surface":
        return import_module(".generateMaps", __name__).generate_map_surface
    if name == "draw_map_surface":
        return import_module(".generateMaps", __name__).draw_map_surface
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")