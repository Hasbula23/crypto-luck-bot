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

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    # Ждём 5 секунд перед стартом, чтобы Render успокоился
    await asyncio.sleep(5)
    
    # Пытаемся удалить вебхук на всякий случай
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except:
        pass
    
    # Запускаем API в потоке
    threading.Thread(target=run_fastapi, daemon=True).start()
    
    print("✅ CryptoLuck запущен и работает")
    
    # Бесконечный цикл с переподключением при ошибке
    while True:
        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        except Exception as e:
            print(f"Ошибка: {e}. Переподключаюсь через 5 секунд...")
            await asyncio.sleep(5)
        else:
            break

if __name__ == "__main__":
    asyncio.run(main())
