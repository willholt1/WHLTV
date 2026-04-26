import argparse
from . import constants as c
from awpy import Demo, ParquetDemo
from awpy.stats import adr, rating



def validate_rating(demo, parquet_demo):
    try:
        rating_from_dem = rating(demo).sort(["steamid", "side"])
        rating_from_parquet = rating(parquet_demo).sort(["steamid", "side"])
        assert rating_from_dem.equals(rating_from_parquet)
        print("Rating check passed.")
    except AssertionError as e:
        print("Rating check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(rating_from_dem)
        print(rating_from_parquet)

def validate_adr(demo, parquet_demo):
    try:
        adr_from_dem = adr(demo, team_dmg=True, self_dmg=False).sort(["steamid", "side"])
        adr_from_parquet = adr(parquet_demo, team_dmg=True, self_dmg=False).sort(["steamid", "side"])
        assert adr_from_dem.equals(adr_from_parquet)
        print("ADR check passed.")
    except AssertionError as e:
        print("ADR check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(adr_from_dem)
        print(adr_from_parquet)

def validate_rounds(demo, parquet_demo):
    try:
        cols = demo.rounds.columns
        demo_df = demo.rounds[cols].sort(list(cols))
        parquet_df = parquet_demo.rounds[cols].sort(list(cols))
        assert demo_df.equals(parquet_df)
        print("Rounds check passed.")
    except AssertionError as e:
        print("Rounds check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)

def validate_header(demo, parquet_demo):
    try:
        assert demo.header["map_name"] == parquet_demo.header["map_name"]
        assert demo.header["patch_version"] == parquet_demo.header["patch_version"]
        print("Header check passed.")
    except AssertionError as e:
        print("Header check failed: Dicts do not match between Demo and ParquetDemo.")
        print(f"dem: map_name: {demo.header['map_name']}, patch_version: {demo.header['patch_version']}")
        print(f"parquet: map_name: {parquet_demo.header['map_name']}, patch_version: {parquet_demo.header['patch_version']}")

def validate_detected_events(demo, parquet_demo):
    try:
        demo_filtered = [e for e in demo.detected_events if e not in c.UNTRACKED_EVENTS]
        parquet_filtered = [e for e in parquet_demo.detected_events if e not in c.COMPOSITE_EVENTS and e is not None]
        assert sorted(demo_filtered, key=lambda x: (str(type(x)), x)) == \
            sorted(parquet_filtered, key=lambda x: (str(type(x)), x))
        print("Detected Events check passed.")
    except AssertionError as e:
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
        assert sorted(demo.default_events, key=lambda x: (str(type(x)), x)) == \
            sorted(parquet_demo.default_events, key=lambda x: (str(type(x)), x))
        print("Default Events check passed.")
    except AssertionError as e:
        print("Default Events check failed: Lists do not match between Demo and ParquetDemo.")
        print(sorted(demo.default_events, key=lambda x: (str(type(x)), x)))
        print(sorted(parquet_demo.default_events, key=lambda x: (str(type(x)), x)))

def validate_server_cvars(demo, parquet_demo):
    try:
        cols = demo.server_cvars.columns
        demo_df = demo.server_cvars[cols].sort(list(cols))
        parquet_df = parquet_demo.server_cvars[cols].sort(list(cols))
        assert demo_df.equals(parquet_df)
        print("Server CVars check passed.")
    except AssertionError as e:
        print("Server CVars check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)

def validate_player_round_totals(demo, parquet_demo):
    try:
        cols = demo.player_round_totals.columns
        demo_df = demo.player_round_totals[cols].sort(list(cols))
        parquet_df = parquet_demo.player_round_totals[cols].sort(list(cols))
        assert demo_df.equals(parquet_df)
        print("Player Round Totals check passed.")
    except AssertionError as e:
        print("Player Round Totals check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)

def validate_bomb(demo, parquet_demo):
    try:
        cols = demo.bomb.columns
        demo_df = demo.bomb[cols].sort(list(cols))
        parquet_df = parquet_demo.bomb[cols].sort(list(cols))
        assert demo_df.equals(parquet_df)
        print("Bomb check passed.")
    except AssertionError as e:
        print("Bomb check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)

def validate_shots(demo, parquet_demo):
    try:
        cols = demo.shots.columns
        demo_df = demo.shots[cols].sort(list(cols))
        parquet_df = parquet_demo.shots[cols].sort(list(cols))
        assert demo_df.equals(parquet_df)
        print("Shots check passed.")
    except AssertionError as e:
        print("Shots check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)

def validate_footsteps(demo, parquet_demo):
    try:
        cols = demo.footsteps.columns
        demo_df = demo.footsteps[cols].sort(list(cols))
        parquet_df = parquet_demo.footsteps[cols].sort(list(cols))
        assert demo_df.equals(parquet_df)
        print("Footsteps check passed.")
    except AssertionError as e:
        print("Footsteps check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)

def validate_damages(demo, parquet_demo):
    try:
        cols = demo.damages.columns
        demo_df = demo.damages[cols].sort(list(cols))
        parquet_df = parquet_demo.damages[cols].sort(list(cols))
        assert demo_df.equals(parquet_df)
        print("Damages check passed.")
    except AssertionError as e:
        print("Damages check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)

def validate_kills(demo, parquet_demo):
    try:
        cols = demo.kills.columns
        demo_df = demo.kills[cols].sort(list(cols))
        parquet_df = parquet_demo.kills[cols].sort(list(cols))
        assert demo_df.equals(parquet_df)
        print("Kills check passed.")
    except AssertionError as e:
        print("Kills check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)

def validate_smokes(demo, parquet_demo):
    try:
        cols = demo.smokes.columns
        demo_df = demo.smokes[cols].sort(list(cols))
        parquet_df = parquet_demo.smokes[cols].sort(list(cols))
        assert demo_df.equals(parquet_df)
        print("Smokes check passed.")
    except AssertionError as e:
        print("Smokes check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)

def validate_infernos(demo, parquet_demo):
    try:
        cols = demo.infernos.columns
        demo_df = demo.infernos[cols].sort(list(cols))
        parquet_df = parquet_demo.infernos[cols].sort(list(cols))
        assert demo_df.equals(parquet_df)
        print("Infernos check passed.")
    except AssertionError as e:
        print("Infernos check failed: DataFrames do not match between Demo and ParquetDemo.")
        print(demo_df)
        print(parquet_df)


def main():
    parser = argparse.ArgumentParser(description="Verify Parquet vs Demo output.")
    parser.add_argument('--demo_file', type=str, help='Path to demo file')
    parser.add_argument('--parquet_file', type=str, help='Path to parquet file')
    parser.add_argument('--patch_version', type=str, help='Patch version to use for ParquetDemo')
    parser.add_argument('--map_name', type=str, help='Map name to use for ParquetDemo')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    debug = args.debug
    demo_file = args.demo_file
    map_name = args.map_name
    parquet_file = args.parquet_file
    patch_version = args.patch_version
    
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

if __name__ == "__main__":
	main()
