import asyncio
import threading
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from api_routes import app
import uvicorn

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

from user_handlers import register_user_handlers
from admin_handlers import register_admin_handlers

register_user_handlers(dp)
register_admin_handlers(dp)

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    # ✅ Жёсткий сброс ВСЕХ старых подключений
    await bot.delete_webhook(drop_pending_updates=True)
    threading.Thread(target=run_api, daemon=True).start()
    print("✅ CryptoLuck запущен на новом токене")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())