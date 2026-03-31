from datetime import datetime, timezone
import re, json
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from urllib.parse import urljoin
import logging
logger = logging.getLogger("hltv.parse")

from models import MatchData, Player, StatLine, Side, Map, Veto, VetoAction, MapResult, map_from_str, vetoaction_from_str
from .serialise import DataclassEnumEncoder

def parse_EventArchive(soup):
    print("Parsing events...")
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
    print("Parsing attending teams...")
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
    print("Parsing rankings...")
    
    teams = []
    for team_div in soup.select('.ranked-team'):
        try:
            rank = int(team_div.select_one('.position').text.strip('#'))
            name = team_div.select_one('.name').text.strip()

            print(f"Team: {name} (rank {rank})")

            points_text = team_div.select_one('.points').text
            points = int(''.join(filter(str.isdigit, points_text)))

            teams.append((name, points, rank))
        except Exception as e:
            print(f"Skipping team due to parse error: {e}")
            continue
    return teams

def parse_Results(soup):
    print("Parsing event results...")
    results = []
    for result in soup.select('.result-con > a.a-reset'):
        try:
            team1Name = result.select_one('.team1 .team').get_text(strip=True)
            team2Name = result.select_one('.team2 .team').get_text(strip=True)
            
            link = result["href"]
            hltvMatchURL = f"https://www.hltv.org{link}"

            raw_map_text = result.select_one('.map-text').get_text(strip=True).lower()

            match = re.fullmatch(r'bo(\d+)', raw_map_text, flags=re.IGNORECASE)
            if match:
                bestOf = int(match.group(1))
            else:
                bestOf = 1  # any map name means best-of-one

            results.append((team1Name, team2Name, hltvMatchURL, bestOf))

        except Exception as e:
            print(f"Skipping team due to parse error: {e}")
            continue
    return results

def parse_MatchData(soup, matchID):
    print("Parsing match data...")
    try:
        # Date
        date_el = soup.select_one(".date[data-unix]")
        matchDate = (
            datetime.fromtimestamp(int(date_el["data-unix"]) / 1000, tz=timezone.utc)
            if date_el and date_el.has_attr("data-unix")
            else None
        )

        # Match notes
        note_el = soup.select_one(".preformatted-text")

        # Demo link
        a = soup.select_one(".vod-popup .vod-text-box a[href^='/download/demo/']")
        demoLink = urljoin("https://www.hltv.org", a["href"]) if a and a.has_attr("href") else None

        md = MatchData(
            matchID = matchID,
            matchDate = matchDate,
            matchNotes = (note_el.get_text(strip=True) if note_el else None),
            demoLink = demoLink,
            matchVeto = [],
            players = [],
            results = []
        )

        md.matchVeto = parse_Veto(soup)
        md.results = parse_map_results(soup)
        playerStats = parse_match_results(soup, matchID)
        
        if playerStats != None:
            md.players.extend(playerStats.values())
        else:
            return None
        
        return json.dumps(md, cls=DataclassEnumEncoder, ensure_ascii=False)
    
    except Exception as e:
        print(f"Skipping team due to error: {e}")
        return None
    
def parse_map_results(soup):
    results = []

    for holder in soup.select(".mapholder"):
        map_name_el = holder.select_one(".mapname")
        if not map_name_el:
            continue

        map_name = map_name_el.get_text(strip=True)
        map_id = map_from_str(map_name)
        if not map_id:
            continue

        left_score_el = holder.select_one(".results-left .results-team-score")
        right_score_el = holder.select_one(".results-right .results-team-score")
        half_score_el = holder.select_one(".results-center-half-score")

        if not left_score_el or not right_score_el:
            continue

        left_score_text = left_score_el.get_text(strip=True)
        right_score_text = right_score_el.get_text(strip=True)

        # Skip unplayed maps
        if left_score_text == "-" or right_score_text == "-":
            continue

        try:
            team1_score = int(left_score_text)
            team2_score = int(right_score_text)
        except ValueError:
            continue

        # Default regulation side scores
        team1_t = 0
        team1_ct = 0
        team2_t = 0
        team2_ct = 0

        # Only try to parse regulation side scores if the half-score block exists
        if half_score_el:
            # Important:
            # HLTV uses class="t"/"ct" for regulation side scores.
            # OT blocks appear afterwards as plain spans without t/ct classes.
            # So we only take the first 4 classified spans.
            side_spans = half_score_el.select("span.t, span.ct")

            if len(side_spans) >= 4:
                regulation_spans = side_spans[:4]

                for i, span in enumerate(regulation_spans):
                    try:
                        score = int(span.get_text(strip=True))
                    except ValueError:
                        continue

                    classes = span.get("class", [])
                    side = "t" if "t" in classes else "ct"

                    # Positions:
                    # 0 = first half, left team
                    # 1 = first half, right team
                    # 2 = second half, left team
                    # 3 = second half, right team
                    if i in (0, 2):  # team1 (left side)
                        if side == "t":
                            team1_t += score
                        else:
                            team1_ct += score
                    else:  # team2 (right side)
                        if side == "t":
                            team2_t += score
                        else:
                            team2_ct += score

        results.append(MapResult(
            mapID=map_id,
            team1Score=team1_score,
            team2Score=team2_score,
            team1TScore=team1_t,
            team1CTScore=team1_ct,
            team2TScore=team2_t,
            team2CTScore=team2_ct
        ))

    return results

def parse_Veto(soup):
    # Pick the veto box that is NOT the notes box
    container = None
    for box in soup.select("div.veto-box"):
        padding = box.select_one(".padding")
        classes = (padding.get("class") or []) if padding else []
        if padding and "preformatted-text" not in classes:
            container = padding
            break

    if not container:
        return []

    vetos: List[Veto] = []

    for row in container.find_all("div", recursive=False):
        raw_line = row.get_text(" ", strip=True)
        if not raw_line:
            continue

        # 1) Normalize whitespace so 'was  left   over' etc. still match
        line = re.sub(r"\s+", " ", raw_line).strip()

        # Case: "<n>. <Map> was left over" / "left over" / "(decider)"
        m1 = re.match(
            r"""^(\d+)\.\s*                      # step number
                 ([A-Za-z0-9 +\-']+?)\s+         # map name
                 (?:was\s+)?left\s*[- ]?over     # 'left over' / 'left-over'
                 (?:\s*\(decider\))?\s*$         # optional (decider)
            """,
            line, re.IGNORECASE | re.VERBOSE,
        )
        if m1:
            step = int(m1.group(1))
            map_name = m1.group(2).strip()
            map_id: Optional[Map] = map_from_str(map_name) or map_from_str(map_name.replace(" ", ""))

            if map_id:
                vetos.append(Veto(
                    stepNumber=step,
                    teamName="",
                    vetoActionID=VetoAction.REMAINING,
                    mapID=map_id
                ))
            else:
                logger.warning("Veto decider: unrecognized map %r (line=%r)", map_name, raw_line)
            continue

        # Case: "<n>. <Team> removed|banned|ban|picked|pick <Map>"
        m2 = re.match(
            r"""^(\d+)\.\s*                      # step number
                 (.+?)\s+                        # team name
                 (removed|banned|ban|picked|pick)\s+
                 ([A-Za-z0-9 +\-']+)\s*$         # map
            """,
            line, re.IGNORECASE | re.VERBOSE,
        )
        if m2:
            step = int(m2.group(1))
            team = m2.group(2).strip()
            verb = m2.group(3).strip()
            map_name = m2.group(4).strip()

            action = vetoaction_from_str(verb)
            if not action:
                logger.warning("Veto verb not recognized %r (line=%r)", verb, raw_line)
                continue

            map_id: Optional[Map] = map_from_str(map_name) or map_from_str(map_name.replace(" ", ""))
            if not map_id:
                logger.warning("Veto map not recognized %r (line=%r)", map_name, raw_line)
                continue

            vetos.append(Veto(
                stepNumber=step,
                teamName=team,
                vetoActionID=action,
                mapID=map_id
            ))
            continue

        # Unmatched line: log with %r so hidden chars show up
        logger.warning("Unmatched veto step: %r", raw_line)

    vetos.sort(key=lambda v: v.stepNumber)
    return vetos

def parse_match_results(soup, matchID):
# Get players and init player objects
    alias_to_player: Dict[str, Player] = {}
    for lineup in soup.select(".lineups .lineup.standard-box"):
        team_name_el = lineup.select_one(".box-headline .text-ellipsis") or lineup.select_one(".box-headline")
        team_name = team_name_el.get_text(strip=True) if team_name_el else None
        for a in lineup.select(".players a[href^='/player/']"):
            nick_el = a.select_one(".player-nick")
            alias = (nick_el.get_text(strip=True) if nick_el else a.get_text(strip=True)) if a else None
            if alias and alias not in alias_to_player:
                alias_to_player[alias] = Player(alias=alias, team=team_name, stats=[])

    # Map tabs are expected on all pages - if missing, log + skip
    map_tabs = soup.select(".stats-menu-link .dynamic-map-name-full")
    if not map_tabs:
        logger.warning(
            "No map tabs found; skipping stats parse. match_id=%s",
            matchID
        )
        return

    for tab in map_tabs:
        map_name = tab.get_text(strip=True)
        m_id = map_from_str(map_name)

        # skip aggregate stats
        if map_name.lower() in ("all maps", "all"):
            continue

        if not m_id:
            logger.warning(
                "Unrecognized map name '%s'; skipping this map. match_id=%s",
                map_name, matchID
            )
            continue

        tab_id = tab.get("id")
        container = soup.find(id=f"{tab_id}-content") if tab_id else None
        if not container:
            logger.warning(
                "Missing stats container for tab id '%s'; skipping. match_id=%s",
                tab_id, matchID
            )
            continue

        # rating version
        rv_el = container.select_one("tr.header-row .rating .ratingDesc")
        rv = rv_el.get_text(strip=True) if rv_el else "3.0"

        # Grab ALL T and CT tables (there are usually two of each — one per team)
        t_tbls  = container.select("table.table.tstats")
        ct_tbls = container.select("table.table.ctstats")

        tables = []
        tables += [(tbl, Side.T) for tbl in t_tbls]
        tables += [(tbl, Side.CT) for tbl in ct_tbls]

        for tbl, side_id in tables:
            for tr in tbl.select("tr"):
                if tr.select_one("th"):
                    continue
                
                # Robust alias extraction: prefer .player-nick, then any <a>, then cell text
                players_td = tr.select_one("td.players")
                if not players_td:
                    continue
                
                nick_el = players_td.select_one(".player-nick")
                if nick_el:
                    alias = nick_el.get_text(strip=True)
                else:
                    a = players_td.select_one("a")
                    alias = (a.get_text(strip=True) if a else players_td.get_text(strip=True)).strip()

                if not alias:
                    continue
                
                # KD -> kills/deaths
                kd_el = tr.select_one("td.kd")
                kills = deaths = 0
                if kd_el:
                    m = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", kd_el.get_text(strip=True))
                    if m:
                        kills, deaths = int(m.group(1)), int(m.group(2))

                # ADR
                adr_el = tr.select_one("td.adr")
                try:
                    adr = float(adr_el.get_text(strip=True)) if adr_el else 0.0
                except ValueError:
                    adr = 0.0

                # Swing %
                swing_el = tr.select_one("td.roundSwing")
                swing = None
                if swing_el:
                    s = swing_el.get_text(strip=True).replace("%", "")
                    try:
                        swing = float(s)
                    except ValueError:
                        swing = None

                # Rating
                rating_el = tr.select_one("td.rating")
                try:
                    rating = float(rating_el.get_text(strip=True)) if rating_el else 0.0
                except ValueError:
                    rating = 0.0

                # Ensure Player exists
                if alias in alias_to_player:
                    alias_to_player[alias].stats.append(StatLine(
                        mapID=m_id, sideID=side_id, kills=kills, deaths=deaths,
                        ADR=adr, swingPct=swing, HLTVRating=rating, HLTVRatingVersion=rv
                    ))
    return alias_to_player