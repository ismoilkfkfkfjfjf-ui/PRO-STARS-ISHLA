import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Supreme Bot Owner (Bosh Ega - 6 bilan boshlanuvchi yagona eng katta ega)
BOT_OWNER_ID = 618430308

admins_raw = os.getenv("ADMINS", "618430308,8422157752")
INITIAL_ADMINS = [int(admin_id.strip()) for admin_id in admins_raw.split(",") if admin_id.strip().isdigit()]

DEFAULT_REF_BONUS = int(os.getenv("DEFAULT_REF_BONUS", "2"))
MIN_WITHDRAW = int(os.getenv("MIN_WITHDRAW", "15"))
PORT = int(os.getenv("PORT", "8080"))

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")
