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
        abs_tol=_FLOAT_ATOL,
        rel_tol=0.0,
    )


def validate_rating(demo, parquet_demo):
    try:
        rating_from_dem = rating(demo).sort(["steamid", "side"])
        rating_from_parquet = rating(parquet_demo).sort(["steamid", "side"])
        _assert_frames_equal(rating_from_dem, rating_from_parquet)
        print("Rating check passed.")
    except AssertionError:
        print("Rating check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(rating_from_dem)
        print(rating_from_parquet)


def validate_adr(demo, parquet_demo):
    try:
        adr_from_dem = adr(demo, team_dmg=True, self_dmg=False).sort(["steamid", "side"])
        adr_from_parquet = adr(parquet_demo, team_dmg=True, self_dmg=False).sort(["steamid", "side"])
        _assert_frames_equal(adr_from_dem, adr_from_parquet)
        print("ADR check passed.")
    except AssertionError:
        print("ADR check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(adr_from_dem)
        print(adr_from_parquet)


def validate_rounds(demo, parquet_demo):
    try:
        cols = demo.rounds.columns
        demo_df = demo.rounds[cols].sort(list(cols))
        parquet_df = parquet_demo.rounds[cols].sort(list(cols))
        _assert_frames_equal(demo_df, parquet_df)
        print("Rounds check passed.")
    except AssertionError:
        print("Rounds check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)


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
    try:
        cols = demo.server_cvars.columns
        demo_df = demo.server_cvars[cols].sort(list(cols))
        parquet_df = parquet_demo.server_cvars[cols].sort(list(cols))
        _assert_frames_equal(demo_df, parquet_df)
        print("Server CVars check passed.")
    except AssertionError:
        print("Server CVars check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)


def validate_player_round_totals(demo, parquet_demo):
    try:
        cols = demo.player_round_totals.columns
        demo_df = demo.player_round_totals[cols].sort(list(cols))
        parquet_df = parquet_demo.player_round_totals[cols].sort(list(cols))
        _assert_frames_equal(demo_df, parquet_df)
        print("Player Round Totals check passed.")
    except AssertionError:
        print("Player Round Totals check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)


def validate_bomb(demo, parquet_demo):
    try:
        cols = demo.bomb.columns
        demo_df = demo.bomb[cols].sort(list(cols))
        parquet_df = parquet_demo.bomb[cols].sort(list(cols))
        _assert_frames_equal(demo_df, parquet_df)
        print("Bomb check passed.")
    except AssertionError:
        print("Bomb check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)


def validate_shots(demo, parquet_demo):
    try:
        cols = demo.shots.columns
        demo_df = demo.shots[cols].sort(list(cols))
        parquet_df = parquet_demo.shots[cols].sort(list(cols))
        _assert_frames_equal(demo_df, parquet_df)
        print("Shots check passed.")
    except AssertionError:
        print("Shots check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)


def validate_footsteps(demo, parquet_demo):
    try:
        cols = demo.footsteps.columns
        demo_df = demo.footsteps[cols].sort(list(cols))
        parquet_df = parquet_demo.footsteps[cols].sort(list(cols))
        _assert_frames_equal(demo_df, parquet_df)
        print("Footsteps check passed.")
    except AssertionError:
        print("Footsteps check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)


def validate_damages(demo, parquet_demo):
    try:
        cols = demo.damages.columns
        demo_df = demo.damages[cols].sort(list(cols))
        parquet_df = parquet_demo.damages[cols].sort(list(cols))
        _assert_frames_equal(demo_df, parquet_df)
        print("Damages check passed.")
    except AssertionError:
        print("Damages check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)


def validate_kills(demo, parquet_demo):
    try:
        cols = demo.kills.columns
        demo_df = demo.kills[cols].sort(list(cols))
        parquet_df = parquet_demo.kills[cols].sort(list(cols))
        _assert_frames_equal(demo_df, parquet_df)
        print("Kills check passed.")
    except AssertionError:
        print("Kills check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)


def validate_smokes(demo, parquet_demo):
    try:
        cols = demo.smokes.columns
        demo_df = demo.smokes[cols].sort(list(cols))
        parquet_df = parquet_demo.smokes[cols].sort(list(cols))
        _assert_frames_equal(demo_df, parquet_df)
        print("Smokes check passed.")
    except AssertionError:
        print("Smokes check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)


def validate_infernos(demo, parquet_demo):
    try:
        cols = demo.infernos.columns
        demo_df = demo.infernos[cols].sort(list(cols))
        parquet_df = parquet_demo.infernos[cols].sort(list(cols))
        _assert_frames_equal(demo_df, parquet_df)
        print("Infernos check passed.")
    except AssertionError:
        print("Infernos check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)


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
