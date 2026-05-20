import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
import uvicorn

# Импортируем хендлеры
from user_handlers import register_user_handlers
from admin_handlers import register_admin_handlers
from api_routes import router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрируем команды бота
register_user_handlers(dp)
register_admin_handlers(dp)

# Создаём FastAPI приложение
app = FastAPI()

# Добавляем CORS (чтобы WebApp мог стучаться к API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем маршруты из api_routes с префиксом /api
app.include_router(router, prefix="/api")

# Корневой маршрут для проверки работы API
@app.get("/")
def root():
    return {"status": "CryptoLuck API is running"}

# Эндпоинт для вебхука Telegram
@app.post(f"/webhook/{BOT_TOKEN}")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"status": "ok"}

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
