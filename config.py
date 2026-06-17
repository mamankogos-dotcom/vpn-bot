import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MARZBAN_URL = os.getenv("MARZBAN_URL", "http://127.0.0.1:8000")
MARZBAN_USER = os.getenv("MARZBAN_USER")
MARZBAN_PASS = os.getenv("MARZBAN_PASS")
SUB_DAYS = int(os.getenv("SUB_DAYS", "30"))
PRICE_STARS = int(os.getenv("PRICE_STARS", "100"))
