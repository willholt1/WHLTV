from . import fetchPage as fp
from . import parseHTML as ph
import json

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


def getMatchPages():
    print("pulling matches from DB...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    try:
        cur.execute("""
                    SELECT matchid, hltvmatchpageurl
                    FROM tblmatches t
                    WHERE NOT EXISTS(SELECT 1 FROM tblmatchmaps t2 WHERE t2.matchid = t.matchid and team1score IS NOT NULL);
                    """)
        rows = cur.fetchall()
            
        matches = []
        for row in rows:
            match = {"matchid": row[0], "hltvurl": row[1] }
            matches.append(match)
        
        return matches

    except Exception as e:
        print(f"Error fetching match pages: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def updateMatchScores(matchID, matchpageJSON):
    print(f"updating match scores for {matchID}...")

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT dbo.udf_set_match_results(%s::jsonb, %s);",
            (matchpageJSON, matchID)
        )
        conn.commit()
    except Exception as e:
        print(f"Error inserting match data: {e}")
        return []
    finally:
        cur.close()
        conn.close()

print("Testing DB connection and fetching match pages...")
matchURLs = getMatchPages()
for match in matchURLs:
    soup = fp.fetchPage(match["hltvurl"], "stats-content")
    matchDataJson = ph.parse_MatchData(soup, match["matchid"])
        
    if matchDataJson is not None:
        updateMatchScores(match["matchid"], matchDataJson)


