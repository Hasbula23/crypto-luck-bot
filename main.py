import asyncio
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.filters import Command
from config import BOT_TOKEN
import uvicorn

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==================== ХЕНДЛЕРЫ (ВСЕ КОМАНДЫ) ====================
from user_handlers import register_user_handlers
from admin_handlers import register_admin_handlers

register_user_handlers(dp)
register_admin_handlers(dp)

# ==================== ДОПОЛНИТЕЛЬНО (на всякий случай) ====================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    from database import register_user
    register_user(message.from_user.id, message.from_user.username)
    await message.reply("🔥 Добро пожаловать в CryptoLuck! Используй /cryptoluck_admin для админки.")

@dp.message(Command("cryptoluck_admin"))
async def admin_cmd(message: types.Message):
    from config import ADMIN_ID
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ Нет доступа")
        return
    from admin_handlers import admin_kb
    await message.reply("🛡 Админ-панель", reply_markup=admin_kb)

# ==================== FASTAPI WEBHOOK ====================
app = FastAPI()

@app.post(f"/webhook/{BOT_TOKEN}")
async def webhook(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    webhook_url = f"https://crypto-luck-final.onrender.com/webhook/{BOT_TOKEN}"
    await bot.set_webhook(webhook_url, drop_pending_updates=True)
    print(f"✅ Webhook установлен: {webhook_url}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
