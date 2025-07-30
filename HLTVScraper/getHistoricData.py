import argparse
import scrapeEvents as se
import scrapeTeamRankings as sr
from datetime import datetime, timedelta
import time

def rankings():
    # Start date of first cs2 event - IEM sydney 2023. NOTE: HLTV only have historic pages for monday dates
    start_date = datetime(2023, 10, 16) 
    end_date = datetime.today()

    # Generate list of dates in 7-day increments
    dates = []
    current_date = start_date
    while current_date <= end_date:
        new_date = {"date": current_date, "day": current_date.day, "month": current_date.strftime("%B").lower(), "year": current_date.year}
        dates.append(new_date)
        current_date += timedelta(days=7)

    for date in dates:
        print(f"Pulling data for {date['date']}")

        # Valve rankings only exist for dates after 2024/01/01
        if date['date'] < datetime(2024, 1, 1):
            skipValve = True
        else:
            skipValve = False

        print("Loading HLTV rankings with Selenium...")
        hltvSoup = sr.fetch_ranking_page(f"https://www.hltv.org/ranking/teams/{date['year']}/{date['month']}/{date['day']}")
        
        print("Parsing HLTV rankings...")
        hltvTeams = sr.parse_rankings(hltvSoup)

        if not skipValve:
            print("Loading Valve rankings with Selenium...")
            valveSoup = sr.fetch_ranking_page(f"https://www.hltv.org/valve-ranking/teams/{date['year']}/{date['month']}/{date['day']}")
            print("Parsing Valve rankings...")
            valveTeams = sr.parse_rankings(valveSoup)
            combinedRanking = sr.join_team_rankings(hltvTeams, valveTeams)
        else:
            print(f"Skipping Valve rankings for {date['date']}...")

            combinedRanking = []
            for name, hltv_points, hltv_rank in hltvTeams:
                combinedRanking.append((name, hltv_points, hltv_rank, None, None))
        

        print(f"Inserting {len(combinedRanking)} teams into the database for date {date['date']}...")
        sr.update_database(combinedRanking, date['date'])

        time.sleep(20)

    print("Done.")

def events():
    print("TODO: Pull historic event data")

def main():
    parser = argparse.ArgumentParser(description="A script that pulls historic HLTV ranking/event data")
    parser.add_argument("case", choices=["1", "2"], help="Choose 1 for Rankings or 2 for Events")
    args = parser.parse_args()

    if args.case == "1":
        rankings()
    elif args.case == "2":
        events()

if __name__ == "__main__":
    main()
