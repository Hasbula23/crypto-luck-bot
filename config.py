import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("NEW_BOT_TOKEN")  # Берём из переменной NEW_BOT_TOKEN
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
CRYPTO_WALLET = os.getenv("CRYPTO_WALLET")
MIN_BET = 5
REK = 0.05
WEBAPP_URL = "https://verdant-tartufo-048198.netlify.app"
