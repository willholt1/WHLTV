from demoparser2 import DemoParser
import os
import re
import sys
import traceback

import pandas as pd
from models import enums

from . import conversion_constants as c


def _log(message: str) -> None:
    print(message, file=sys.stderr)


def demoToParquet(demoPaths, output_dir="ParquetFiles"):
    map_groups = get_map_groups(demoPaths)
    if not map_groups:
        raise RuntimeError("No valid demos could be grouped for conversion.")

    created_files = {}

    os.makedirs(output_dir, exist_ok=True)

    for map_name, map_data in map_groups.items():
        all_tick_data, full_event_df = get_demo_data(map_data["demos"])
        full_combined = merge_event_tick_data(all_tick_data, full_event_df)

        parquet_path = os.path.join(output_dir, generate_parquet_filename(map_data["demos"][0][0], map_name))

        _log(f"Writing data for map {map_name} to {parquet_path}...")
        full_combined.to_parquet(parquet_path, index=False)

        created_files[enums.de_map_from_str(map_name)] = [parquet_path, map_data["patch_version"]]
    return created_files


def merge_event_tick_data(all_tick_data, full_event_df):
    clean_steamID_cols(all_tick_data, "steamid")
    clean_steamID_cols(full_event_df, "user_steamid")
    clean_steamID_cols(full_event_df, "steamid")

    _log("Merging tick and event data...")
    full_combined = pd.concat([all_tick_data, full_event_df], ignore_index=True)

    if "reason" in full_combined.columns:
        full_combined["reason"] = full_combined["reason"].astype("string")
    return full_combined


def get_demo_data(demos):
    tick_data_list = []
    event_dfs = []
    tick_offset = 0

    for demoPath, _ in sorted(demos, key=lambda x: x[1]):
        stage = "initialization"
        try:
            parser = DemoParser(demoPath)

            stage = "parse_ticks"
            _log(f"Parsing ticks from {demoPath}")
            tick_data = parser.parse_ticks(c.TRACKED_TICK_PROPS)

            for col in c.TICK_COLS:
                if col in tick_data.columns:
                    tick_data[col] += tick_offset

            tick_data_list.append(tick_data)

            stage = "parse_grenades"
            _log("Parsing grenade data")
            df = pd.DataFrame(parser.parse_grenades())
            df["event_type"] = "grenade_data"
            for col in c.TICK_COLS:
                if col in df.columns:
                    df[col] += tick_offset
            event_dfs.append(df)

            non_player_events = {"server_cvar"}

            for event in c.TRACKED_EVENTS:
                stage = f"parse_event:{event}"
                _log(f"Parsing event: {event} from {demoPath}")
                if event in non_player_events:
                    df = pd.DataFrame(parser.parse_event(event))
                else:
                    df = pd.DataFrame(parser.parse_event(event, player=c.DEFAULT_PLAYER_PROPS, other=c.DEFAULT_WORLD_PROPS))

                if df.empty:
                    continue

                df["event_type"] = event
                for col in c.TICK_COLS:
                    if col in df.columns:
                        df[col] += tick_offset
                event_dfs.append(df)

            if "tick" in tick_data.columns and not tick_data.empty:
                tick_offset += tick_data["tick"].max() + 1

        except BaseException as ex:
            if isinstance(ex, (KeyboardInterrupt, SystemExit)):
                raise
            _log(
                f"Skipping demo {demoPath} at stage '{stage}' due to "
                f"{type(ex).__name__}: {ex}"
            )
            _log(traceback.format_exc())
            continue

    if not tick_data_list:
        raise RuntimeError("No demos could be parsed successfully.")

    all_tick_data = pd.concat(tick_data_list, ignore_index=True)
    full_event_df = pd.concat(event_dfs, ignore_index=True) if event_dfs else pd.DataFrame()

    return all_tick_data, full_event_df


def get_map_groups(demoPaths):
    map_groups = {}

    for demoPath in demoPaths:
        stage = "header_grouping"
        try:
            if os.path.getsize(demoPath) == 0:
                _log(f"Skipping empty demo file: {demoPath}")
                continue

            stage = "parse_header"
            parser = DemoParser(demoPath)
            header = parser.parse_header()
            map_name = header["map_name"]
            patch_version = header["patch_version"]

            stage = "parse_total_rounds_played"
            rounds_df = parser.parse_ticks(["total_rounds_played"])
            total_rounds_played = rounds_df["total_rounds_played"].max() if "total_rounds_played" in rounds_df else 0

            _log(f"Grouped demo {demoPath}: map={map_name}, patch={patch_version}, rounds={total_rounds_played}")

            if map_name not in map_groups:
                map_groups[map_name] = {"patch_version": patch_version, "demos": []}
            map_groups[map_name]["demos"].append((demoPath, total_rounds_played))

        except BaseException as ex:
            if isinstance(ex, (KeyboardInterrupt, SystemExit)):
                raise
            _log(
                f"Skipping demo {demoPath} at stage '{stage}' due to "
                f"{type(ex).__name__}: {ex}"
            )
            _log(traceback.format_exc())
            continue

    return map_groups


def generate_parquet_filename(demo_path, map_name):
    filename = os.path.basename(demo_path)
    name_no_ext = filename.rsplit(".", 1)[0]

    parts = name_no_ext.split("-")

    last = parts[-1]
    has_part_suffix = re.fullmatch(r"p\d+", last) is not None

    if has_part_suffix:
        base = "-".join(parts[:-2])
    else:
        base = "-".join(parts[:-1])

    parquet_name = f"{base}-{map_name}.parquet"
    return parquet_name


def clean_steamID_cols(df: pd.DataFrame, column_name: str) -> None:
    if column_name in df.columns:
        df[column_name] = df[column_name].astype(str)
        df.loc[df[column_name].isin(["None", "nan", "NaN", "<NA>"]), column_name] = None
