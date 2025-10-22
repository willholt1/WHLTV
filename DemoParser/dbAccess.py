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
def get_player_teams(matchid):
    print("Extracting player teams from DB...")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM dbo.udf_get_match_players(%s);", (matchid,))
        rows = cur.fetchall()

        playerTeams = []
        for row in rows:
            playerTeam = {"teamid": row[0], "teamName": row[1], "playerID": row[2], "alias": row[3], "steamID": row[4]}
            playerTeams.append(playerTeam)

        return playerTeams

    except Exception as e:
        print(f"Error fetching player teams: {e}")
        return []
    finally:
        cur.close()
        conn.close()