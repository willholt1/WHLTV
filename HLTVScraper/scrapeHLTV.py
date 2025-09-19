import argparse
from datetime import datetime, timedelta
import time
import fetchPage as fp
import parseHTML as ph
import dbAccess as db
import utility as u
import logging

from pathlib import Path
from bs4 import BeautifulSoup

logging.basicConfig(
    filename="scraper.log",  # Log file
    level=logging.INFO,      # Minimum level to log
    format="%(asctime)s [%(levelname)s] %(message)s"
)
# Suppress webdriver-manager INFO logs
logging.getLogger("WDM").setLevel(logging.WARNING)

def scrapeCurrentRankings():
    hltvSoup = fp.fetchPage("https://www.hltv.org/ranking/teams", "ranked-team")

    valveSoup = fp.fetchPage("https://www.hltv.org/valve-ranking/teams", "ranked-team")

    hltvTeams = ph.parse_Rankings(hltvSoup)
    valveTeams = ph.parse_Rankings(valveSoup)

    combinedRanking = u.util_JoinTeamRankings(hltvTeams, valveTeams)

    db.insertTeamRankings(combinedRanking)

    print("Done.")

def scrapeHistoricRankings():
    # Start date of first cs2 event - IEM sydney 2023. NOTE: HLTV only have historic pages for monday dates
    startDate = datetime(2023, 10, 16) 
    endDate = datetime.today()

    # Generate list of dates in 7-day increments
    dates = []
    currentDate = startDate
    while currentDate <= endDate:
        new_date = {"date": currentDate, "day": currentDate.day, "month": currentDate.strftime("%B").lower(), "year": currentDate.year}
        dates.append(new_date)
        currentDate += timedelta(days=7)

    for date in dates:
        print(f"Pulling data for {date['date']}")

        # Valve rankings only exist for dates after 2024/01/01
        if date['date'] < datetime(2024, 1, 1):
            skipValve = True
        else:
            skipValve = False

        hltvSoup = fp.fetchPage(f"https://www.hltv.org/ranking/teams/{date['year']}/{date['month']}/{date['day']}", "ranked-team")

        if hltvSoup is None:
            print(f"Skipping {date['date']} - HLTV rankings not found.")
            continue

        print("Parsing HLTV rankings...")
        hltvTeams = ph.parse_Rankings(hltvSoup)

        if not skipValve:
            valveSoup = fp.fetchPage(f"https://www.hltv.org/valve-ranking/teams/{date['year']}/{date['month']}/{date['day']}", "ranked-team")
            
            if valveSoup is None:
                print(f"Skipping {date['date']} - Valve rankings not found.")
                continue
            
            print("Parsing Valve rankings...")
            valveTeams = ph.parse_Rankings(valveSoup)
            combinedRanking = u.util_JoinTeamRankings(hltvTeams, valveTeams)
        else:
            print(f"Skipping Valve rankings for {date['date']}...")

            combinedRanking = []
            for name, hltv_points, hltv_rank in hltvTeams:
                combinedRanking.append((name, hltv_points, hltv_rank, None, None))
        
        db.insertTeamRankings(combinedRanking, date['date'])

        time.sleep(20)

    print("Done.")

def scrapeRecentEvents():
    hltvSoup = fp.fetchPage("https://www.hltv.org/events/archive", "small-event")

    events = ph.parse_EventArchive(hltvSoup)

    db.insertEvents(events)

    print("Done.")

def scrapeHistoricEvents():

    stopDate = datetime(2023, 10, 16)
    loop = True
    i = 0
    while loop:
        print(f"Offset: {i}")
        
        if i == 0:
            hltvSoup = fp.fetchPage("https://www.hltv.org/events/archive", "small-event")
        elif i > 0:
            hltvSoup = fp.fetchPage(f"https://www.hltv.org/events/archive?offset={i}", "small-event")
        
        if hltvSoup is None:
            print(f"Skipping offset: {i} due to error")
            continue

        events = ph.parse_EventArchive(hltvSoup)

        db.insertEvents(events)

        print("Checking event dates...")
        # Index 2 refers to start date of the event
        if any(row[2] is not None and row[2].replace(tzinfo=None) < stopDate.replace(tzinfo=None) for row in events):
            loop = False

        i += 50

    print("Done.")

def scrapeAttendingTeams():
    events = db.getHighValueEvents()

    for event in events:
        print(event["hltvurl"])
        
        eventSoup = fp.fetchPage(event["hltvurl"], "team-box")

        if eventSoup is None:
            print(f"Skipping eventID {event['eventid']} due to error")
            continue

        attendingTeams = ph.parse_EventPage_GetAttendingTeams(eventSoup)

        db.insertEventTeams(event["eventid"], attendingTeams)
        
    print("Done.")

def scrapeEventResults():
    resultsPages = db.getResultsPages()

    for resultsPage in resultsPages:
        resultsSoup = fp.fetchPage(resultsPage["hltvResultsPageURL"], "result-con")

        results = ph.parse_Results(resultsSoup)

        db.insertMatch(resultsPage["eventid"], results)

def scrapeMatchData():
    # get match URLs
    matchURLs = db.getMatchPages()

    for match in matchURLs:
        soup = fp.fetchPage(match["hltvMatchPageURL"], "stats-content")
        matchDataJson = ph.parse_MatchData(soup, match["matchid"])
        
        db.insertMatchData(matchDataJson)
    
    print("Done.")


def main():
    parser = argparse.ArgumentParser(description="A script that pulls historic HLTV ranking/event data")
    parser.add_argument("case", choices=["1", "2", "3", "4", "5", "6", "7", "10"], help="Choose 1/2 for Rankings (current/historic) \n3/4 for Events (recent/historic)\n5 for teams attending high value events\n6 for Event results \n7 for match data \n10 for all recent data")
    args = parser.parse_args()

    if args.case == "1":
        scrapeCurrentRankings()
    elif args.case == "2":
        scrapeHistoricRankings()
    elif args.case == "3":
        scrapeRecentEvents()
    elif args.case == "4":
        scrapeHistoricEvents()
    elif args.case == "5":
        scrapeAttendingTeams()
    elif args.case == "6":
        scrapeEventResults()
    elif args.case == "7":
        scrapeMatchData()
    elif args.case == "10":
        scrapeCurrentRankings()
        scrapeRecentEvents()
        scrapeAttendingTeams()
        db.markEventsForDownload()
        scrapeEventResults()
        scrapeMatchData()

if __name__ == "__main__":
    main()
