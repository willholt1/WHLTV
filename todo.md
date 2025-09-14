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
- [x] scrape matches
    - [x] event results page match data
        - [x] team1
        - [x] team2
        - [x] match URL
        - [x] best of
    - [x] match page data
        - [x] veto data
        - [x] match notes
        - [x] team1 players
        - [x] team2 players
        - [x] demo download link
        - [ ] match date
        - [x] HLTV stats per map per side
            - [x] Player
            - [x] kills
            - [x] deaths
            - [x] ADR
            - [x] swing %
            - [x] HLTV rating version
            - [x] HLTV rating
- [ ] Download Demo
    - [ ] get link to demo from DB
    - [ ] download demo zip
    - [ ] create file structure
    - [ ] Extract zip to correct folder
    - [ ] save paths to DB

## Database

### Scraper data
- [x] Team names
- [x] Team rankings
- [x] Events - prize pool/LAN/Location
- [x] Teams attending events
- [x] Matches - Teams/Best of x/HLTV match page
- [x] Veto data
    - [x] ERD
    - [x] Create tables
    - [x] Create procs
- [x] Match notes i.e. Quarterfinal
- [x] Team rosters for match - how can these be matched to the steamIDs from the demos?
- [x] Maps 
    - [ ] map versions??
- [x] HLTV stats? under own tables as the data is already aggregated 

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