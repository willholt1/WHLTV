from demoparser2 import DemoParser
import pandas as pd
import constants as c
import numpy as np

def demoToParquet(demoPaths, parquetPath):
    tick_data_list = []
    event_dfs = []
    tick_offset = 0

    for demoPath in demoPaths:
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
    

    all_tick_data = pd.concat(tick_data_list, ignore_index=True)#.copy()
    full_event_df = pd.concat(event_dfs, ignore_index=True)#.copy()
   
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

    full_combined.to_parquet(parquetPath, index=False)

