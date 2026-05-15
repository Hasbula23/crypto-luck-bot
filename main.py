import os
import random
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from supabase import create_client
from fastapi import FastAPI, Request
import uvicorn
import asyncio
import threading

load_dotenv()

# ========== КОНФИГ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
CRYPTO_WALLET = os.getenv("CRYPTO_WALLET")
MIN_BET = 5
REK = 0.05

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()

# ========== ФУНКЦИИ ==========
def register_user(tg_id, username):
    try:
        user = supabase.table("users").select("*").eq("telegram_id", tg_id).execute()
        if not user.data:
            supabase.table("users").insert({
                "telegram_id": tg_id,
                "username": username or str(tg_id),
                "balance": 0,
                "total_bet": 0,
                "total_win": 0,
                "created_at": datetime.now().isoformat()
            }).execute()
    except Exception as e:
        print(f"DB Error: {e}")

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Играть", web_app=WebAppInfo(url="https://verdant-tartufo-048198.netlify.app"))],
        [InlineKeyboardButton(text="💼 Кошелек", callback_data="wallet"), InlineKeyboardButton(text="📊 Топ игроков", callback_data="top")],
        [InlineKeyboardButton(text="👑 Проверить честность", callback_data="fair")]
    ])

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Пополнить баланс"), KeyboardButton(text="💰 Баланс игрока")],
        [KeyboardButton(text="📋 Все игроки"), KeyboardButton(text="🔙 Выйти из админки")]
    ],
    resize_keyboard=True
)

# ========== КОМАНДЫ ==========
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    register_user(message.from_user.id, message.from_user.username)
    await message.reply(
        f"🔥 Добро пожаловать в CryptoLuck!\n💰 Мин. ставка: {MIN_BET} USDT\n⚡ Рейк: 5%\n👇 Играть:",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("cryptoluck_admin"))
async def secret_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ Доступ запрещён.")
        return
    await message.reply("🛡 Админ-панель", reply_markup=admin_kb)

@dp.callback_query(lambda c: c.data == "wallet")
async def wallet_cmd(callback: types.CallbackQuery):
    user = supabase.table("users").select("balance").eq("telegram_id", callback.from_user.id).execute()
    balance = user.data[0]['balance'] if user.data else 0
    await callback.message.answer(f"💵 Баланс: {balance} USDT\n💳 Кошелек: `{CRYPTO_WALLET}`", parse_mode="MARKDOWN")
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
    await callback.message.answer("🔐 Provably Fair будет в следующей версии.")
    await callback.answer()

# ========== АДМИН-ОБРАБОТЧИКИ ==========
@dp.message(lambda message: message.text == "➕ Пополнить баланс" and message.from_user.id == ADMIN_ID)
async def admin_add_balance_start(message: types.Message):
    await message.reply("Введите ID и сумму через пробел.\nПример: `7955348018 100`")

@dp.message(lambda message: message.text and message.text[0].isdigit() and len(message.text.split()) == 2 and message.from_user.id == ADMIN_ID)
async def admin_add_balance_confirm(message: types.Message):
    try:
        user_id, amount = message.text.split()
        user_id, amount = int(user_id), float(amount)
        user = supabase.table("users").select("balance").eq("telegram_id", user_id).execute()
        if user.data:
            new_bal = user.data[0]['balance'] + amount
            supabase.table("users").update({"balance": new_bal}).eq("telegram_id", user_id).execute()
            await message.reply(f"✅ Начислено {amount} USDT. Новый баланс: {new_bal}")
        else:
            await message.reply("❌ Пользователь не найден.")
    except:
        await message.reply("❌ Ошибка. Формат: `ID СУММА`")

@dp.message(lambda message: message.text == "💰 Баланс игрока" and message.from_user.id == ADMIN_ID)
async def admin_balance_start(message: types.Message):
    await message.reply("Введите ID пользователя:")

@dp.message(lambda message: message.text.isdigit() and message.from_user.id == ADMIN_ID)
async def admin_show_balance(message: types.Message):
    user_id = int(message.text)
    user = supabase.table("users").select("username, balance").eq("telegram_id", user_id).execute()
    if user.data:
        await message.reply(f"👤 {user.data[0]['username']}\n💰 Баланс: {user.data[0]['balance']} USDT")
    else:
        await message.reply("❌ Не найден.")

@dp.message(lambda message: message.text == "📋 Все игроки" and message.from_user.id == ADMIN_ID)
async def admin_list_users(message: types.Message):
    users = supabase.table("users").select("username, balance").order("balance", desc=True).limit(20).execute()
    text = "📋 Топ-20:\n\n"
    for u in users.data:
        text += f"🔹 {u['username']} — {u['balance']} USDT\n"
    await message.reply(text)

@dp.message(lambda message: message.text == "🔙 Выйти из админки" and message.from_user.id == ADMIN_ID)
async def admin_exit(message: types.Message):
    await message.reply("🔒 Выход", reply_markup=types.ReplyKeyboardRemove())

# ========== API ==========
@app.post("/api/play")
async def play_game(request: Request):
    data = await request.json()
    tg_id, bet, choice = data.get("tg_id"), float(data.get("bet")), data.get("choice")
    user = supabase.table("users").select("balance").eq("telegram_id", tg_id).execute()
    if not user.data or user.data[0]['balance'] < bet or bet < MIN_BET:
        return {"status": "error", "message": f"Мин. ставка {MIN_BET} USDT или не хватает средств"}
    result = random.choice(["heads", "tails"])
    win = (result == choice)
    win_amount = bet - (bet * REK) if win else 0
    new_balance = user.data[0]['balance'] + (win_amount if win else -bet)
    supabase.table("users").update({"balance": new_balance}).eq("telegram_id", tg_id).execute()
    return {"status": "success", "result": result, "win": win, "new_balance": new_balance}

@app.get("/api/balance")
async def get_balance(tg_id: int):
    user = supabase.table("users").select("balance").eq("telegram_id", tg_id).execute()
    return {"balance": user.data[0]['balance'] if user.data else 0, "min_bet": MIN_BET}

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    threading.Thread(target=run_fastapi, daemon=True).start()
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())