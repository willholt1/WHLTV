import argparse
from datetime import datetime, timedelta
import time
import fetchPage as fp
import parseHTML as ph
import dbAccess as db
import utility as u
import logging

logging.basicConfig(
    filename="scraper.log",  # Log file
    level=logging.INFO,      # Minimum level to log
    format="%(asctime)s [%(levelname)s] %(message)s"
)
# Suppress webdriver-manager INFO logs
logging.getLogger("WDM").setLevel(logging.WARNING)

def scrapeCurrentRankings():
    print("Loading HLTV rankings with Selenium...")
    hltvSoup = fp.fetchPage("https://www.hltv.org/ranking/teams", "ranked-team")

    print("Loading Valve rankings with Selenium...")
    valveSoup = fp.fetchPage("https://www.hltv.org/valve-ranking/teams", "ranked-team")

    print("Parsing rankings...")
    hltvTeams = ph.parse_Rankings(hltvSoup)
    valveTeams = ph.parse_Rankings(valveSoup)

    combinedRanking = u.util_JoinTeamRankings(hltvTeams, valveTeams)

    print(f"Inserting {len(combinedRanking)} teams into the database...")
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

        print("Loading HLTV rankings with Selenium...")
        hltvSoup = fp.fetchPage(f"https://www.hltv.org/ranking/teams/{date['year']}/{date['month']}/{date['day']}", "ranked-team")

        if hltvSoup is None:
            print(f"Skipping {date['date']} - HLTV rankings not found.")
            continue

        print("Parsing HLTV rankings...")
        hltvTeams = ph.parse_Rankings(hltvSoup)

        if not skipValve:
            print("Loading Valve rankings with Selenium...")
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
        

        print(f"Inserting {len(combinedRanking)} teams into the database for date {date['date']}...")
        db.insertTeamRankings(combinedRanking, date['date'])

        time.sleep(20)

    print("Done.")

def scrapeRecentEvents():
    print("Loading HLTV events with Selenium...")
    hltvSoup = fp.fetchPage("https://www.hltv.org/events/archive", "small-event")

    print("Parsing events...")
    events = ph.parse_EventArchive(hltvSoup)

    print(f"Inserting {len(events)} teams into the database...")
    db.insertEvents(events)

    print("Done.")

def scrapeHistoricEvents():

    stopDate = datetime(2023, 10, 16)
    loop = True
    i = 0
    while loop:
        print("Loading HLTV events with Selenium...")
        print(f"Offset: {i}")
        
        if i == 0:
            hltvSoup = fp.fetchPage("https://www.hltv.org/events/archive", "small-event")
        elif i > 0:
            hltvSoup = fp.fetchPage(f"https://www.hltv.org/events/archive?offset={i}", "small-event")
        
        if hltvSoup is None:
            print(f"Skipping offset: {i} due to error")
            continue

        print("Parsing events...")
        events = ph.parse_EventArchive(hltvSoup)

        print(f"Inserting {len(events)} teams into the database...")
        db.insertEvents(events)

        print("Checking event dates...")
        # Index 2 refers to start date of the event
        if any(row[2] is not None and row[2].replace(tzinfo=None) < stopDate.replace(tzinfo=None) for row in events):
            loop = False

        i += 50

    print("Done.")

def scrapeAttendingTeams():
    print("Extracting event list from DB...")
    events = db.getHighValueEvents()

    for event in events:
        print("Loading HLTV event page with Selenium...")
        print(event["hltvurl"])
        
        eventSoup = fp.fetchPage(event["hltvurl"], "team-box")

        if eventSoup is None:
            print(f"Skipping eventID {event['eventid']} due to error")
            continue

        print("Parsing teams...")
        attendingTeams = ph.parse_EventPage_GetAttendingTeams(eventSoup)

        print(f"Inserting {len(attendingTeams)} teams into the DB for eventID {event['eventid']}...")
        print(attendingTeams)
        db.insertEventTeams(event["eventid"], attendingTeams)
        
    print("Done.")

def scrapeEventResults():
    resultsPages = db.getResultsPages()

    for resultsPage in resultsPages:
        print("Loading HLTV results page with Selenium...")
        resultsSoup = fp.fetchPage(resultsPage["hltvResultsPageURL"], "result-con")

        print("Parsing results...")
        results = ph.parse_Results(resultsSoup)

        print(f"Inserting {len(results)} matches into the DB for eventID {resultsPage['eventid']}...")
        db.insertMatch(resultsPage["eventid"], results)


def main():
    parser = argparse.ArgumentParser(description="A script that pulls historic HLTV ranking/event data")
    parser.add_argument("case", choices=["1", "2", "3", "4", "5", "6", "10"], help="Choose 1/2 for Rankings (current/historic) \n3/4 for Events (recent/historic)\n5 for teams attending high value events\n6 for TODO ---------\n10 for all recent data")
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
    elif args.case == "10":
        scrapeCurrentRankings()
        scrapeRecentEvents()
        scrapeAttendingTeams()
        db.markEventsForDownload()

if __name__ == "__main__":
    main()
