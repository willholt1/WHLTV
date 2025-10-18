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

    merged.to_parquet(parquetPath, index=False)