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

def insertTeamRankings(teams, date = None):
    
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    for name, hltv_points, hltv_rank, valve_points, valve_rank in teams:
        cur.execute("""
            CALL dbo."usp_InsertTeamRanking"(%s, %s, %s, %s, %s, %s)
        """, (name, hltv_points, hltv_rank, valve_points, valve_rank, date))

    conn.commit()
    cur.close()
    conn.close()


def insertEvents(events):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    for name, prize_pool, start_date, end_date, event_type, location, url in events:
        try:
            cur.execute("""
                CALL dbo.usp_InsertEvent(%s::TEXT, %s::TEXT, %s::TIMESTAMPTZ, %s::TIMESTAMPTZ,
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

def getHighValueEvents():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM dbo.udf_gethighvalueevents();")
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


def insertEventTeams(eventID, teams):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    try:
        cur.execute(
            "CALL dbo.usp_inserteventteams(%s, %s);",
            (eventID, teams)
        )
        conn.commit()
    except Exception as e:
        print(f"Error inserting teams: {e}")
        return []
    finally:
        cur.close()
        conn.close()