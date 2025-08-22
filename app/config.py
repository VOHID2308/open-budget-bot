import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN   = os.getenv("BOT_TOKEN", "")
ADMIN_IDS   = {int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x}
DB_PATH     = os.getenv("DB_PATH", "openbudget_leaderboard.db")

PORTAL_URL  = os.getenv("PORTAL_URL", "https://openbudget.uz/")
BOARDS_URL  = os.getenv("BOARDS_URL", "https://openbudget.uz/boards")
REGION_NAME = os.getenv("REGION_NAME", "Urgut (Gʻoʻs)")

VOTE_URL = os.getenv("VOTE_URL", "https://openbudget.uz/boards/initiatives/initiative/52/98a9fe5d-2824-478c-92f4-f09a309fc10e")



SEASON_ID   = os.getenv("SEASON_ID", "2025-II")
