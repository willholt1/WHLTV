# WHLTV
## Scraper
- [x] scrape team rankings
    - [x] HLTV
    - [x] VRS
- [x] scrape played events
    - [x] get event pages for potentailly high value events
    - [x] get teams attending
    - [x] get results pages
    - [x] mark events with a top 10 team in attendence for download
- [ ] scrape matches
    - [x] event results page match data
        - [x] team1
        - [x] team2
        - [x] match URL
        - [x] best of
    - [ ] match page data
        - [ ] veto data
        - [ ] match notes
        - [ ] team1 players
        - [ ] team2 players
        - [ ] HLTV stats per map per side
            - [ ] Player
            - [ ] kills
            - [ ] deaths
            - [ ] ADR
            - [ ] swing %
            - [ ] HLTV rating version
            - [ ] HLTV rating
    - [ ] Download Demo
        - [ ] Extract zip + save paths to DB

## Database

### Scraper data
- [x] Team names
- [x] Team rankings
- [x] Events - prize pool/LAN/Location
- [x] Teams attending events
- [x] Matches - Teams/Best of x/HLTV match page
- [ ] Veto data
    - [x] ERD
    - [x] Create tables
    - [ ] Create procs
- [ ] Match notes i.e. Quarterfinal
- [ ] Team rosters for match - how can these be matched to the steamIDs from the demos?
- [ ] Maps - map versions??
- [ ] HLTV stats? under own tables as the data is already aggregated 

### Demo meta data
- [ ] date downloaded
- [ ] demo file path
- [ ] parser version
- [ ] date parsed

### Demo data
- [ ] Match up demo player alias to playerID in DB
#### Round data
- [ ] Detect and store round boundaries (freeze/live/end).
- [ ] Capture bomb objective events (plant start, plant end, defuse start/end) and round-end reason.
- [ ] Store round result (winner/loser)

#### Economy data
- [ ] Store per-round per-team economy snapshot 
    - [ ] total start money
    - [ ] total team spend
    - [ ] total team equip value
    - [ ] loss-bonus tier
- [ ] Player inventory timeline
    - [ ] PlayerID
    - [ ] Round number
    - [ ] Primary weapon ID
    - [ ] Secondary weapon ID
    - [ ] Armour (none/kevlar/helmet)
    - [ ] Kit
    - [ ] Flash count
    - [ ] HE count
    - [ ] Molly count
    - [ ] CT molly count
    - [ ] Smoke count

#### Player action data
- [ ] DemoID
- [ ] Tick
- [ ] Player X
- [ ] Player Y
- [ ] Player Z

##### Enemy spotted data
- [ ] Tick
- [ ] Aim data? crosshair placement
- [ ] Spotted player X
- [ ] Spotted player Y
- [ ] Spotted player Z

##### Combat data
- [ ] Attacking player ID
- [ ] Victim player ID
- [ ] Weapon ID
- [ ] Scoped (bool)
- [ ] Damage dealt
- [ ] Tick

##### Utility
- [ ] GrenadeID
- [ ] Grenade pop X
- [ ] Grenade pop Y
- [ ] Grenade pop Z
- [ ] Effect duration
- [ ] Total damage per player
- [ ] Flash affect per player



## API

## Data warehouse

## Frontend