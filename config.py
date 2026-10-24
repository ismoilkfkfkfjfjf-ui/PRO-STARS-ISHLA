import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8871643647:AAHVylckulkVw6Y156fgB8PretV1FD03RCQ").strip()

admins_raw = os.getenv("ADMINS", "618430308,8422157752")
INITIAL_ADMINS = [int(admin_id.strip()) for admin_id in admins_raw.split(",") if admin_id.strip().isdigit()]

# Super admins who cannot be removed by other admins
SUPER_ADMINS = [618430308, 8422157752]

DEFAULT_REF_BONUS = int(os.getenv("DEFAULT_REF_BONUS", "2"))
MIN_WITHDRAW = int(os.getenv("MIN_WITHDRAW", "15"))
PORT = int(os.getenv("PORT", "8080"))

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")
