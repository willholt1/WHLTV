import pandas as pd
import constants as c
import dbAccess as db

def generate_scoreboard(match_id, parquet_path):
    # --- LOAD DATA ---
    # Load player teams from the database
    player_teams_df = pd.DataFrame(db.get_player_teams(match_id))
    player_teams_df['alias'] = player_teams_df['alias'].astype(str).str.lower()

    print(f"Loading game data from {parquet_path}...")
    df = pd.read_parquet(parquet_path)

    print("Calculating K/D...")
    deaths_df = df[df['event_type'] == 'player_death']

    kills_df = (
        deaths_df.groupby('attacker_name', dropna=True)
        .size()
        .reset_index(name='kills')
    )

    deaths_count_df = (
        deaths_df.groupby('player_name', dropna=True)
        .size()
        .reset_index(name='deaths')
    )


    print("Calculating ADR...")
    round_count = df['total_rounds_played'].max()
    damage_df = df[df['event_type'] == 'player_hurt'].copy()

    # Need health from previous tick to avoid damage values exceeding current health
    prev_health = (
        df[['tick', 'steamid', 'health_x']]
        .rename(columns={'tick': 'prev_tick', 'health_x': 'prev_health'})
    )

    # Merge to get victim's previous health
    damage_df['prev_tick'] = damage_df['tick'] - 1
    damage_df = damage_df.merge(prev_health, on=['prev_tick', 'steamid'], how='left')

    # Calculate effective damage
    damage_df['effective_damage'] = damage_df[['dmg_health', 'prev_health']].min(axis=1)
    damage_df['effective_damage'] = damage_df['effective_damage'].fillna(damage_df['dmg_health'])

    # Filter and de-duplicate
    damage_df = (
        damage_df[
            damage_df['attacker_name'].notna()
        ][['attacker_name', 'player_name', 'dmg_health', 'prev_health', 'effective_damage']]
        .drop_duplicates()
    )

    # Calculate ADR
    adr_df = (
        damage_df.groupby('attacker_name', dropna=True)['effective_damage']
        .sum()
        .reset_index(name='ADR')
    )

    adr_df['ADR'] = adr_df['ADR'] / max(round_count, 1)  # avoid divide by zero

    
    print("Compiling scoreboard...")
    kd_df = (
        kills_df
        .merge(deaths_count_df, left_on='attacker_name', right_on='player_name', how='outer')
        .merge(adr_df, on='attacker_name', how='outer')
        .fillna(0)
        .rename(columns={'attacker_name': 'playername'})
        [['playername', 'kills', 'deaths', 'ADR']]
    )

    kd_df['playername'] = kd_df['playername'].astype(str).str.lower()

    # --- SCOREBOARD ---

    scoreboard = (
        kd_df
        .merge(player_teams_df, left_on='playername', right_on='alias', how='left')
        [['teamName', 'playername', 'kills', 'deaths', 'ADR']]
        .sort_values(by=['teamName', 'kills'], ascending=[True, False])
        .reset_index(drop=True)
    )
    print(round_count)
    return scoreboard
