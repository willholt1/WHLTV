from datetime import datetime, timezone

def parse_EventArchive(soup):
    events = []

    for event in soup.select("a.small-event"):
        try:
            # Event URL
            link = event["href"]
            full_url = f"https://www.hltv.org{link}"

            # Event name
            name = event.select_one(".event-col .text-ellipsis").text.strip()

            # Prize pool
            prize_td = event.select_one(".prizePoolEllipsis")
            prize_pool = prize_td["title"].strip() if prize_td and prize_td.has_attr("title") else prize_td.text.strip()

            # Event type (Online, LAN, etc.)
            event_type = event.select_one("td.gtSmartphone-only")
            event_type = event_type.text.strip() if event_type else None

            # Start and end dates
            date_spans = event.select("tr.eventDetails span[data-unix]")

            start_date = datetime.fromtimestamp(int(date_spans[0]["data-unix"]) / 1000, tz=timezone.utc) if len(date_spans) >= 1 else None
            end_date = datetime.fromtimestamp(int(date_spans[1]["data-unix"]) / 1000, tz=timezone.utc) if len(date_spans) >= 2 else None
            
            # Location
            location_span = event.select_one("tr.eventDetails .col-desc")
            location = location_span.text.strip().split("|")[0] if location_span else None

            events.append((
                name,
                prize_pool,
                start_date,
                end_date,
                event_type,
                location,
                full_url
            ))


        except Exception as e:
            print(f"Skipping event due to error: {e}")
            continue

    return events

def parse_EventPage_GetAttendingTeams(soup):
    teams = []

    for team in soup.select(".team-box"):
        try:
           name = team.select_one(".team-name .text").get_text(strip=True)
           teams.append(name)

        except Exception as e:
            print(f"Skipping team due to error: {e}")
            continue

    return teams

def parse_Rankings(soup):
    teams = []
    for team_div in soup.select('.ranked-team'):
        try:
            rank = int(team_div.select_one('.position').text.strip('#'))
            name = team_div.select_one('.name').text.strip()

            points_text = team_div.select_one('.points').text
            points = int(''.join(filter(str.isdigit, points_text)))

            teams.append((name, points, rank))
        except Exception as e:
            print(f"Skipping team due to parse error: {e}")
            continue
    return teams