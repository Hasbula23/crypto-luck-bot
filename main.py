import asyncio
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
import uvicorn

# Прямой импорт твоего API
from api_routes import app as api_app

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрируем хендлеры
from user_handlers import register_user_handlers
from admin_handlers import register_admin_handlers

register_user_handlers(dp)
register_admin_handlers(dp)

# Объединяем FastAPI приложение с твоими маршрутами
app = FastAPI()

# Монтируем твои маршруты из api_routes
app.mount("/api", api_app)

# Корневой маршрут для проверки
@app.get("/")
def root():
    return {"status": "CryptoLuck API is running"}

async def main():
    # Устанавливаем вебхук
    webhook_url = f"https://crypto-luck-final.onrender.com/webhook/{BOT_TOKEN}"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    print(f"✅ Webhook установлен: {webhook_url}")
    
    # Запускаем FastAPI сервер
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
