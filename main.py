import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from config import BOT_TOKEN
import uvicorn

# Импорты твоих модулей
from user_handlers import register_user_handlers
from admin_handlers import register_admin_handlers
from api_routes import router

# ==================== ИНИЦИАЛИЗАЦИЯ ====================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрируем все команды бота
register_user_handlers(dp)
register_admin_handlers(dp)

# ==================== FASTAPI ПРИЛОЖЕНИЕ ====================
app = FastAPI(title="CryptoLuck API", description="Элитное казино в Telegram")

# CORS — чтобы твой WebApp мог общаться с API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем маршруты из api_routes (все твои /play, /balance и т.д.)
app.include_router(router, prefix="/api")

# ==================== КОРНЕВЫЕ МАРШРУТЫ ====================
@app.get("/")
async def root():
    """Проверка, что API жив"""
    return {"status": "CryptoLuck API is running", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Для Render health checks"""
    return {"status": "healthy"}

# ==================== ВЕБХУК ДЛЯ TELEGRAM ====================
@app.post(f"/webhook/{BOT_TOKEN}")
async def webhook(request: Request):
    """Telegram шлёт сюда обновления"""
    update_data = await request.json()
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"status": "ok"}

# ==================== ЗАПУСК ====================
async def main():
    # Устанавливаем вебхук
    webhook_url = f"https://crypto-luck-final.onrender.com/webhook/{BOT_TOKEN}"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    print(f"✅ Вебхук установлен: {webhook_url}")
    print(f"✅ API документация: https://crypto-luck-final.onrender.com/docs")

    # Запускаем сервер
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
