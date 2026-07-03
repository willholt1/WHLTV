from awpy import Demo, ParquetDemo
from awpy.stats import adr, rating
import polars as pl
import polars.testing

from . import conversion_constants as c


# Float tolerance for position/velocity columns that differ by a small amount
# when using tick-level lookup vs demoparser2's internal event-level sampling.
_FLOAT_ATOL = 5.0


def _assert_frames_equal(demo_df: pl.DataFrame, parquet_df: pl.DataFrame) -> None:
    """Assert two frames are equal, using float tolerance for numeric columns.

    Row order is not required to match (rows may sort differently due to
    tiny floating-point differences in position columns).
    """
    polars.testing.assert_frame_equal(
        demo_df,
        parquet_df,
        check_row_order=False,
        check_column_order=True,
        # check_dtypes=False: demoparser2 returns health/numeric props as
        # Float64 when attaching via parse_event(player=...) but as Int32
        # when they are native event columns. parse_ticks consistently
        # returns the native game type (Int32). The values are equivalent;
        # only the numeric encoding differs between the two approaches.
        check_dtypes=False,
        abs_tol=_FLOAT_ATOL,
        rel_tol=0.0,
    )


def _check_label(label: str, demo_df: pl.DataFrame, parquet_df: pl.DataFrame) -> None:
    """Run _assert_frames_equal and print a clear pass/fail + reason on failure."""
    try:
        _assert_frames_equal(demo_df, parquet_df)
        print(f"{label} check passed.")
    except AssertionError as e:
        print(f"{label} check failed: {e}")
        print(demo_df)
        print(parquet_df)


def validate_rating(demo, parquet_demo):
    try:
        _check_label("Rating",
            rating(demo).sort(["steamid", "side"]),
            rating(parquet_demo).sort(["steamid", "side"]))
    except Exception as e:
        print(f"Rating check error: {e}")


def validate_adr(demo, parquet_demo):
    try:
        _check_label("ADR",
            adr(demo, team_dmg=True, self_dmg=False).sort(["steamid", "side"]),
            adr(parquet_demo, team_dmg=True, self_dmg=False).sort(["steamid", "side"]))
    except Exception as e:
        print(f"ADR check error: {e}")


def _validate_event(label: str, demo_df: pl.DataFrame, parquet_df: pl.DataFrame) -> None:
    cols = demo_df.columns
    _check_label(label, demo_df[cols].sort(list(cols)), parquet_df[cols].sort(list(cols)))


def validate_header(demo, parquet_demo):
    try:
        assert demo.header["map_name"] == parquet_demo.header["map_name"]
        assert demo.header["patch_version"] == parquet_demo.header["patch_version"]
        print("Header check passed.")
    except AssertionError:
        print("Header check failed: Dicts do not match between Demo and ParquetDemo.")
        print(f"dem: map_name: {demo.header['map_name']}, patch_version: {demo.header['patch_version']}")
        print(f"parquet: map_name: {parquet_demo.header['map_name']}, patch_version: {parquet_demo.header['patch_version']}")


def validate_detected_events(demo, parquet_demo):
    try:
        demo_filtered = [e for e in demo.detected_events if e not in c.UNTRACKED_EVENTS]
        parquet_filtered = [e for e in parquet_demo.detected_events if e not in c.COMPOSITE_EVENTS and e is not None]
        assert sorted(demo_filtered, key=lambda x: (str(type(x)), x)) == sorted(
            parquet_filtered, key=lambda x: (str(type(x)), x)
        )
        print("Detected Events check passed.")
    except AssertionError:
        print("Detected Events check failed: Lists do not match between Demo and ParquetDemo.")
        demo_sorted = sorted(demo_filtered, key=lambda x: (str(type(x)), x))
        parquet_sorted = sorted(parquet_filtered, key=lambda x: (str(type(x)), x))
        demo_set = set(demo_sorted)
        parquet_set = set(parquet_sorted)
        only_in_demo = demo_set - parquet_set
        only_in_parquet = parquet_set - demo_set
        if only_in_demo:
            print(f"  Only in Demo (filtered): {only_in_demo}")
        if only_in_parquet:
            print(f"  Only in Parquet (filtered): {only_in_parquet}")
        if not only_in_demo and not only_in_parquet:
            print("  Lists differ in order or duplicates, but have same unique elements.")


def validate_default_events(demo, parquet_demo):
    try:
        assert sorted(demo.default_events, key=lambda x: (str(type(x)), x)) == sorted(
            parquet_demo.default_events, key=lambda x: (str(type(x)), x)
        )
        print("Default Events check passed.")
    except AssertionError:
        print("Default Events check failed: Lists do not match between Demo and ParquetDemo.")
        print(sorted(demo.default_events, key=lambda x: (str(type(x)), x)))
        print(sorted(parquet_demo.default_events, key=lambda x: (str(type(x)), x)))


def validate_server_cvars(demo, parquet_demo):
    _validate_event("Server CVars", demo.server_cvars, parquet_demo.server_cvars)


def validate_player_round_totals(demo, parquet_demo):
    _validate_event("Player Round Totals", demo.player_round_totals, parquet_demo.player_round_totals)


def validate_bomb(demo, parquet_demo):
    _validate_event("Bomb", demo.bomb, parquet_demo.bomb)


def validate_shots(demo, parquet_demo):
    _validate_event("Shots", demo.shots, parquet_demo.shots)


def validate_footsteps(demo, parquet_demo):
    _validate_event("Footsteps", demo.footsteps, parquet_demo.footsteps)


def validate_damages(demo, parquet_demo):
    _validate_event("Damages", demo.damages, parquet_demo.damages)


def validate_kills(demo, parquet_demo):
    _validate_event("Kills", demo.kills, parquet_demo.kills)


def validate_smokes(demo, parquet_demo):
    _validate_event("Smokes", demo.smokes, parquet_demo.smokes)


def validate_infernos(demo, parquet_demo):
    _validate_event("Infernos", demo.infernos, parquet_demo.infernos)


def validate_rounds(demo, parquet_demo):
    _validate_event("Rounds", demo.rounds, parquet_demo.rounds)


def run_all_validations(
    demo_file: str,
    parquet_file: str,
    patch_version: str,
    map_name: str,
    debug: bool = False,
) -> None:
    demo = Demo(demo_file, verbose=debug)
    demo.parse()

    parquet_demo = ParquetDemo(parquet_file, map_name=map_name, patch_version=patch_version, verbose=debug)
    parquet_demo.parse()

    validate_infernos(demo, parquet_demo)
    validate_smokes(demo, parquet_demo)
    validate_kills(demo, parquet_demo)
    validate_damages(demo, parquet_demo)
    validate_footsteps(demo, parquet_demo)
    validate_shots(demo, parquet_demo)
    validate_bomb(demo, parquet_demo)
    validate_player_round_totals(demo, parquet_demo)
    validate_server_cvars(demo, parquet_demo)
    validate_default_events(demo, parquet_demo)
    validate_detected_events(demo, parquet_demo)
    validate_header(demo, parquet_demo)
    validate_rounds(demo, parquet_demo)
    validate_adr(demo, parquet_demo)
    validate_rating(demo, parquet_demo)
