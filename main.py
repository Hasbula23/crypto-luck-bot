import os
import random
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from supabase import create_client
from fastapi import FastAPI, Request
import uvicorn
import asyncio
import threading

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
CRYPTO_WALLET = os.getenv("CRYPTO_WALLET")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

def register_user(tg_id, username):
    try:
        user = supabase.table("users").select("*").eq("telegram_id", tg_id).execute()
        if not user.data:
            supabase.table("users").insert({
                "telegram_id": tg_id,
                "username": username or str(tg_id),
                "balance": 0
            }).execute()
    except Exception as e:
        print("DB Error:", e)

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Играть", web_app=WebAppInfo(url="https://verdant-tartufo-048198.netlify.app"))],
        [InlineKeyboardButton(text="💼 Кошелек", callback_data="wallet"), InlineKeyboardButton(text="📊 Топ игроков", callback_data="top")],
        [InlineKeyboardButton(text="👑 Проверить честность", callback_data="fair")]
    ])
    return keyboard

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    register_user(message.from_user.id, message.from_user.username)
    await message.reply(
        "🔥 Добро пожаловать в CryptoLuck!\n\n👇 Нажми на кнопку 'Играть', чтобы начать.",
        reply_markup=get_main_keyboard()
    )

# --- АДМИН-КОМАНДА ДЛЯ ПОПОЛНЕНИЯ БАЛАНСА ---
@dp.message(Command("addmoney"))
async def add_money(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("🚫 Недостаточно прав")
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("❌ Ошибка. Пиши: /addmoney 100")
            return
        amount = float(parts[1])
        user_id = message.from_user.id
        user = supabase.table("users").select("balance").eq("telegram_id", user_id).execute()
        if user.data:
            new_bal = user.data[0]['balance'] + amount
            supabase.table("users").update({"balance": new_bal}).eq("telegram_id", user_id).execute()
            await message.reply(f"✅ Баланс увеличен на {amount} USDT. Новый баланс: {new_bal}")
        else:
            await message.reply("❌ Пользователь не найден")
    except:
        await message.reply("❌ Ошибка. Пиши: /addmoney 100")

@dp.callback_query(lambda c: c.data == "wallet")
async def wallet_cmd(callback: types.CallbackQuery):
    user = supabase.table("users").select("balance").eq("telegram_id", callback.from_user.id).execute()
    balance = user.data[0]['balance'] if user.data else 0
    await callback.message.answer(f"💵 Баланс: {balance} USDT\n\n💳 Кошелек для пополнения:\n`{CRYPTO_WALLET}`\n(Только USDT TRC20)", parse_mode="MARKDOWN")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "top")
async def top_cmd(callback: types.CallbackQuery):
    tops = supabase.table("users").select("username, balance").order("balance", desc=True).limit(10).execute()
    text = "🏆 ТОП-10:\n\n"
    for i, u in enumerate(tops.data, 1):
        text += f"{i}. {u['username']} — {u['balance']} USDT\n"
    await callback.message.answer(text)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "fair")
async def fair_cmd(callback: types.CallbackQuery):
    await callback.message.answer("🔐 Provably Fair будет добавлен в обновлении.")
    await callback.answer()

@app.post("/api/play")
async def play_game(request: Request):
    data = await request.json()
    tg_id = data.get("tg_id")
    bet = float(data.get("bet"))
    choice = data.get("choice")

    user = supabase.table("users").select("balance").eq("telegram_id", tg_id).execute()
    if not user.data or user.data[0]['balance'] < bet:
        return {"status": "error", "message": "Недостаточно средств"}

    result = random.choice(["heads", "tails"])
    win = (result == choice)
    
    if win:
        new_balance = user.data[0]['balance'] + bet
        result_msg = "ПОБЕДА! +" + str(bet)
    else:
        new_balance = user.data[0]['balance'] - bet
        result_msg = "ПРОИГРЫШ! -" + str(bet)

    supabase.table("users").update({"balance": new_balance}).eq("telegram_id", tg_id).execute()

    return {
        "status": "success",
        "result": result,
        "win": win,
        "new_balance": new_balance,
        "message": result_msg
    }

@app.get("/api/balance")
async def get_balance(tg_id: int):
    user = supabase.table("users").select("balance").eq("telegram_id", tg_id).execute()
    balance = user.data[0]['balance'] if user.data else 0
    return {"balance": balance}

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    threading.Thread(target=run_fastapi, daemon=True).start()
    print("Бот запущен и работает")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())