from demoparser2 import DemoParser
import pandas as pd
import constants as c

def demoToParquet(demoPath, parquetPath):
    # Initialize parser
    parser = DemoParser(demoPath)

    tick_data = parser.parse_ticks(c.TRACKED_TICK_PROPS)

    event_dfs = []
    for event in c.TRACKED_EVENTS:
        df = parser.parse_event(event)
        df['event_type'] = event  # tag the event type
        event_dfs.append(df)
    full_event_df = pd.concat(event_dfs, ignore_index=True)

    player_events = full_event_df[full_event_df['user_steamid'].notna()].copy()
    non_player_events = full_event_df[full_event_df['user_steamid'].isna()].copy()

    # Fix Type Mismatches for Merging
    tick_data["steamid"] = tick_data["steamid"].astype(str)
    full_event_df["user_steamid"] = full_event_df["user_steamid"].astype(str)

    merged = pd.merge(
        tick_data,
        full_event_df,
        left_on=['tick', 'steamid'], 
        right_on=['tick', 'user_steamid'], 
        how='left'
    )

    non_player_subset = non_player_events[['tick', 'event_type'] + 
        [col for col in non_player_events.columns if col not in ['tick', 'event_type']]
    ]

    for col in merged.columns:
        if col not in non_player_subset.columns:
            non_player_subset[col] = None

    full_combined = pd.concat([merged, non_player_subset[merged.columns]], ignore_index=True)

    full_combined.to_parquet(parquetPath, index=False)