import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432")
}

#########
# Get
#########
def getHighValueEvents():
    print("Extracting event list from DB...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM dbo.udf_get_high_value_events();")
        rows = cur.fetchall()
            
        events = []
        for row in rows:
            event = {"eventid": row[0], "hltvurl": row[1] }
            events.append(event)
        
        return events

    except Exception as e:
        print(f"Error fetching high-value events: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def getResultsPages():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM dbo.udf_get_results_pages();")
        rows = cur.fetchall()
            
        resultsPages = []
        for row in rows:
            resultsPage = {"eventid": row[0], "hltvResultsPageURL": row[1] }
            resultsPages.append(resultsPage)
        
        return resultsPages

    except Exception as e:
        print(f"Error fetching results URLs: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def getMatchPages():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM dbo.udf_get_match_pages();")
        rows = cur.fetchall()
            
        matchPages = []
        for row in rows:
            matchPage = {"matchid": row[0], "hltvMatchPageURL": row[1] }
            matchPages.append(matchPage)
        
        return matchPages

    except Exception as e:
        print(f"Error fetching results URLs: {e}")
        return []
    finally:
        cur.close()
        conn.close()

#########
# Insert
#########
def insertTeamRankings(teams, date = None):
    if date == None:
        print(f"Inserting {len(teams)} teams into the database for date {date}...")
    else:
        print(f"Inserting {len(teams)} teams into the database...")

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    for name, hltv_points, hltv_rank, valve_points, valve_rank in teams:
        cur.execute("""
            CALL dbo.usp_insert_team_ranking(%s, %s, %s, %s, %s, %s)
        """, (name, hltv_points, hltv_rank, valve_points, valve_rank, date))

    conn.commit()
    cur.close()
    conn.close()


def insertEvents(events):
    print(f"Inserting {len(events)} events into the database...")

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    for name, prize_pool, start_date, end_date, event_type, location, url in events:
        try:
            cur.execute("""
                CALL dbo.usp_insert_event(%s::TEXT, %s::TEXT, %s::TIMESTAMPTZ, %s::TIMESTAMPTZ,
                %s::TEXT, %s::TEXT, %s::TEXT)
                """, (
                    name,
                    prize_pool,
                    start_date,
                    end_date,
                    event_type,
                    location,
                    url
                ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Failed to insert event '{name}': {e}")
    
    cur.close()
    conn.close()


def insertEventTeams(eventID, teams):
    print(f"Inserting {len(teams)} teams into the DB for eventID {eventID}...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    try:
        cur.execute(
            "CALL dbo.usp_insert_event_teams(%s, %s);",
            (eventID, teams)
        )
        conn.commit()
    except Exception as e:
        print(f"Error inserting teams: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def insertMatch(eventID, matches):
    print(f"Inserting {len(matches)} matches into the DB for eventID {eventID}...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    for team1Name, team2Name, hltvMatchURL, bestOf in matches:
        try:
            cur.execute("""
                CALL dbo.usp_insert_match(%s, %s, %s, %s, %s)
                """, (
                    eventID,
                    team1Name,
                    team2Name,
                    hltvMatchURL,
                    bestOf
                ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Failed to insert match '{hltvMatchURL}': {e}")
    
    cur.close()
    conn.close()

def insertMatchData(matchDataJson):
    print("Inserting matchpage data...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    try:
        cur.execute(
            "CALL dbo.usp_insert_matchpage_data_from_json(%s::jsonb);",
            (matchDataJson,)
        )
        conn.commit()
    except Exception as e:
        print(f"Error inserting match data: {e}")
        return []
    finally:
        cur.close()
        conn.close()

#########
# Update
#########

def markEventsForDownload():
    print("Marking events for download...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    try:
        cur.execute(
            "CALL usp_mark_events_for_download();"
        )
        conn.commit()
    except Exception as e:
        print(f"Error flagging events: {e}")
        return []
    finally:
        cur.close()
        conn.close()
