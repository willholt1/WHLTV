# Script to run the scraper to update the database with the latest matches and player stats
from . import scrapeHLTV as sh
from . import dbAccess as db
from . import fetchPage as fp

driver = fp.createDriver()

sh.scrapeCurrentRankings(driver)
sh.scrapeRecentEvents(driver)
sh.scrapeAttendingTeams(driver)
db.markEventsForDownload()
sh.scrapeEventResults(driver)
sh.scrapeMatchData(driver)

