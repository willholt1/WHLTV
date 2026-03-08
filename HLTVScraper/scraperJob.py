# Script to run the scraper to update the database with the latest matches and player stats
from . import scrapeHLTV as sh
from . import dbAccess as db

sh.scrapeCurrentRankings()
sh.scrapeRecentEvents()
sh.scrapeAttendingTeams()
db.markEventsForDownload()
sh.scrapeEventResults()
sh.scrapeMatchData()

