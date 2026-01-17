from email import header
from demoparser2 import DemoParser
import pandas as pd
from . import constants as c
import numpy as np
import os
import re
from models import enums

def demoToParquet(demoPaths):
    map_groups = get_map_groups(demoPaths)
    created_files = {}
    map_players = {}

    for map_name, map_data in map_groups.items():
        all_tick_data, full_event_df = get_demo_data(map_data["demos"])
        full_combined = merge_event_tick_data(all_tick_data, full_event_df)

        map_players[enums.de_map_from_str(map_name)] = get_player_names(full_combined)

        parquet_dir = "ParquetFiles"
        os.makedirs(parquet_dir, exist_ok=True)
        parquet_path = os.path.join(parquet_dir, generate_parquet_filename(map_data["demos"][0][0], map_name))

        print(f"Writing data for map {map_name} to {parquet_path}...")
        full_combined.to_parquet(parquet_path, index=False)

        created_files[enums.de_map_from_str(map_name)] = [parquet_path, map_data["patch_version"]]
    return created_files, map_players

def merge_event_tick_data(all_tick_data, full_event_df):
    non_player_events = full_event_df[full_event_df['user_steamid'].isna()].copy()

    # Fix Type Mismatches for Merging
    all_tick_data["steamid"] = all_tick_data["steamid"].astype(str)
    full_event_df["user_steamid"] = full_event_df["user_steamid"].astype(str)

    print("Merging tick and event data...")
    merged = pd.merge(
            all_tick_data,
            full_event_df,
            left_on=['tick', 'steamid'], 
            right_on=['tick', 'user_steamid'], 
            how='left'
        )

    print("Appending non-player events...")
    non_player_subset = non_player_events[['tick', 'event_type'] +
        [col for col in non_player_events.columns if col not in ['tick', 'event_type']]
        ].copy()

    non_player_subset = non_player_subset.reindex(columns=merged.columns)

    # drop all-NA cols to avoid warnings
    non_player_subset = non_player_subset.loc[:, non_player_subset.notna().any()]  

    full_combined = pd.concat([merged, non_player_subset], ignore_index=True)

    # Need to force reason to string to avoid pyarrow issues with mixed types
    # newer demos store "reason" as a string for round_end events
    # but player_disconnect events use ints
    full_combined['reason'] = full_combined['reason'].astype('string')
    return full_combined

def get_demo_data(demos):
    for demoPath, _ in sorted(demos, key=lambda x: x[1]):
        tick_data_list = []
        event_dfs = []
        tick_offset = 0
        # Initialize parser
        parser = DemoParser(demoPath)

        print(f"Parsing ticks from {demoPath}")
        tick_data = parser.parse_ticks(c.TRACKED_TICK_PROPS)
        
        for col in c.TICK_COLS:
            if col in tick_data.columns:
                tick_data[col] += tick_offset

        tick_data_list.append(tick_data)

        for event in c.TRACKED_EVENTS:
            print(f"Parsing event: {event} from {demoPath}")
            df = pd.DataFrame(parser.parse_event(event))
            df['event_type'] = event  # tag the event type
            for col in c.TICK_COLS:
                if col in df.columns:
                    df[col] += tick_offset
            event_dfs.append(df)

        tick_offset += tick_data['tick'].max() + 1
    
    all_tick_data = pd.concat(tick_data_list, ignore_index=True)
    full_event_df = pd.concat(event_dfs, ignore_index=True)

    return all_tick_data,full_event_df

def get_map_groups(demoPaths):
    map_groups = {}
    for demoPath in demoPaths:
        parser = DemoParser(demoPath)
        header = parser.parse_header()
        map_name = header["map_name"]
        patch_version = header["patch_version"]

        total_rounds_played = parser.parse_ticks(["total_rounds_played"])['total_rounds_played'].max()
        
        print(total_rounds_played)
        print(map_name)
        print(patch_version)

        if map_name not in map_groups:
            map_groups[map_name] = {"patch_version": patch_version, "demos": []}
        map_groups[map_name]["demos"].append((demoPath, total_rounds_played))
    return map_groups


def generate_parquet_filename(demo_path, map_name):
    filename = os.path.basename(demo_path)
    name_no_ext = filename.rsplit(".", 1)[0]  # strip extension

    parts = name_no_ext.split("-")

    # Detect if last element matches p1, p2, p10, etc.
    last = parts[-1]
    has_part_suffix = re.fullmatch(r"p\d+", last) is not None

    if has_part_suffix:
        # remove the last part (pX)
        base = "-".join(parts[:-2])  # remove pX AND the map name it follows
    else:
        # remove only the last part (map name)
        base = "-".join(parts[:-1])

    parquet_name = f"{base}-{map_name}.parquet"
    return parquet_name

def get_player_names(df):
    player_names = {}
    for steamid, group in df.groupby('player_steamid'):
        names = group['player_name'].dropna().unique().tolist()
        player_names[steamid] = names
    return player_names