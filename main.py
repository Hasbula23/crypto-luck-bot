import asyncio
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from config import BOT_TOKEN
from user_handlers import register_user_handlers
from admin_handlers import register_admin_handlers
import uvicorn

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

register_user_handlers(dp)
register_admin_handlers(dp)

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

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
