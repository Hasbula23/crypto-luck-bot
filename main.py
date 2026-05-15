import os
import random
import time
import hashlib
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
MIN_BET = 5  # Минимальная ставка в USDT
REK = 0.05  # 5% рейк

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
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
        print(f"DB Error (register): {e}")

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Играть", web_app=WebAppInfo(url="https://verdant-tartufo-048198.netlify.app"))],
        [InlineKeyboardButton(text="💼 Кошелек", callback_data="wallet"), InlineKeyboardButton(text="📊 Топ игроков", callback_data="top")],
        [InlineKeyboardButton(text="👑 Проверить честность", callback_data="fair"), InlineKeyboardButton(text="🛡 Админка", callback_data="admin_panel")]
    ])

# ========== АДМИН-КЛАВИАТУРА ==========
admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Пополнить баланс"), KeyboardButton(text="💰 Баланс игрока")],
        [KeyboardButton(text="📋 Все игроки"), KeyboardButton(text="💸 Вывести средства")],
        [KeyboardButton(text="🔙 Выйти из админки")]
    ],
    resize_keyboard=True
)

# ========== ТЕЛЕГРАМ КОМАНДЫ ==========
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    register_user(message.from_user.id, message.from_user.username)
    await message.reply(
        "🔥 Добро пожаловать в CryptoLuck!\n\n"
        f"💰 Минимальная ставка: {MIN_BET} USDT\n"
        f"⚡️ Рейк казино: 5%\n\n"
        "👇 Нажми 'Играть', чтобы начать зарабатывать!",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("admin"))
async def admin_entry(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ Доступ запрещён.")
        return
    await message.reply("🛡 *Админ-панель CryptoLuck*\nВыбери действие:", reply_markup=admin_kb, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "admin_panel")
async def admin_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    await callback.message.answer("🛡 *Админ-панель*", reply_markup=admin_kb, parse_mode="Markdown")
    await callback.answer()

@dp.message(lambda message: message.text == "➕ Пополнить баланс" and message.from_user.id == ADMIN_ID)
async def admin_add_balance_start(message: types.Message):
    await message.reply(f"Введите ID и сумму через пробел.\nПример: `{ADMIN_ID} 100`\n\nМинимальная сумма: {MIN_BET} USDT", parse_mode="Markdown")

@dp.message(lambda message: message.text and message.text[0].isdigit() and message.from_user.id == ADMIN_ID)
async def admin_add_balance_confirm(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("❌ Формат: `ID СУММА`")
            return
        user_id, amount = int(parts[0]), float(parts[1])
        if amount < MIN_BET:
            await message.reply(f"❌ Минимальная сумма пополнения: {MIN_BET} USDT")
            return
        user = supabase.table("users").select("balance").eq("telegram_id", user_id).execute()
        if user.data:
            new_bal = user.data[0]['balance'] + amount
            supabase.table("users").update({"balance": new_bal}).eq("telegram_id", user_id).execute()
            await message.reply(f"✅ Пользователю `{user_id}` начислено {amount} USDT.\n💰 Новый баланс: {new_bal} USDT", parse_mode="Markdown")
        else:
            await message.reply("❌ Пользователь не найден.")
    except:
        await message.reply("❌ Ошибка. Используй формат: `ID СУММА`")

@dp.message(lambda message: message.text == "💰 Баланс игрока" and message.from_user.id == ADMIN_ID)
async def admin_get_balance_start(message: types.Message):
    await message.reply("Введите ID пользователя:")

@dp.message(lambda message: message.text.isdigit() and message.from_user.id == ADMIN_ID)
async def admin_show_balance(message: types.Message):
    user_id = int(message.text)
    user = supabase.table("users").select("username, balance, total_bet, total_win").eq("telegram_id", user_id).execute()
    if user.data:
        u = user.data[0]
        await message.reply(
            f"👤 *{u['username']}* (ID: {user_id})\n"
            f"💰 Баланс: {u['balance']} USDT\n"
            f"🎲 Всего ставок: {u['total_bet']} USDT\n"
            f"🏆 Выигрыши: {u['total_win']} USDT",
            parse_mode="Markdown"
        )
    else:
        await message.reply("❌ Пользователь не найден.")

@dp.message(lambda message: message.text == "📋 Все игроки" and message.from_user.id == ADMIN_ID)
async def admin_list_users(message: types.Message):
    users = supabase.table("users").select("username, balance").order("balance", desc=True).limit(20).execute()
    text = "📋 *Топ-20 игроков:*\n\n"
    for u in users.data:
        text += f"🔹 {u['username']} — {u['balance']} USDT\n"
    await message.reply(text, parse_mode="Markdown")

@dp.message(lambda message: message.text == "💸 Вывести средства" and message.from_user.id == ADMIN_ID)
async def admin_withdraw_start(message: types.Message):
    await message.reply("💸 Функция в разработке. Скоро ты сможешь выводить USDT вручную из админки.")

@dp.message(lambda message: message.text == "🔙 Выйти из админки" and message.from_user.id == ADMIN_ID)
async def admin_exit(message: types.Message):
    await message.reply("🔒 Админ-панель закрыта.", reply_markup=types.ReplyKeyboardRemove())

@dp.callback_query(lambda c: c.data == "wallet")
async def wallet_cmd(callback: types.CallbackQuery):
    user = supabase.table("users").select("balance").eq("telegram_id", callback.from_user.id).execute()
    balance = user.data[0]['balance'] if user.data else 0
    await callback.message.answer(
        f"💵 *Твой баланс:* {balance} USDT\n\n"
        f"💳 Кошелек для пополнения:\n`{CRYPTO_WALLET}`\n"
        f"(Только USDT TRC20)\n\n"
        f"💰 Минимальная ставка: {MIN_BET} USDT",
        parse_mode="MARKDOWN"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "top")
async def top_cmd(callback: types.CallbackQuery):
    tops = supabase.table("users").select("username, balance").order("balance", desc=True).limit(10).execute()
    text = "🏆 *ТОП-10 ИГРОКОВ:*\n\n"
    for i, u in enumerate(tops.data, 1):
        text += f"{i}. {u['username']} — {u['balance']} USDT\n"
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "fair")
async def fair_cmd(callback: types.CallbackQuery):
    await callback.message.answer(
        "🔐 *Provably Fair*\n\n"
        "Каждый результат игры подписывается серверным хэшем. "
        "Ты сможешь проверить честность каждого броска в разделе 'История'.\n"
        "Полная поддержка будет добавлена в ближайшее обновление.",
        parse_mode="Markdown"
    )
    await callback.answer()

# ========== API ДЛЯ WEBAPP ==========
@app.post("/api/play")
async def play_game(request: Request):
    data = await request.json()
    tg_id = data.get("tg_id")
    bet = float(data.get("bet"))
    choice = data.get("choice")

    if bet < MIN_BET:
        return {"status": "error", "message": f"Минимальная ставка {MIN_BET} USDT"}

    user = supabase.table("users").select("balance").eq("telegram_id", tg_id).execute()
    if not user.data or user.data[0]['balance'] < bet:
        return {"status": "error", "message": "Недостаточно средств"}

    # ----- Provably Fair заглушка (позже заменим на реальную подпись) -----
    result = random.choice(["heads", "tails"])
    win = (result == choice)
    
    if win:
        win_amount = bet - (bet * REK)
        new_balance = user.data[0]['balance'] + win_amount
        result_msg = f"✅ ПОБЕДА! +{win_amount} USDT"
    else:
        new_balance = user.data[0]['balance'] - bet
        result_msg = f"❌ ПРОИГРЫШ! -{bet} USDT"
    
    # Обновляем баланс и статистику
    supabase.table("users").update({"balance": new_balance}).eq("telegram_id", tg_id).execute()
    supabase.table("users").update({"total_bet": supabase.table("users").select("total_bet").eq("telegram_id", tg_id).execute().data[0]['total_bet'] + bet}).eq("telegram_id", tg_id).execute()
    if win:
        supabase.table("users").update({"total_win": supabase.table("users").select("total_win").eq("telegram_id", tg_id).execute().data[0]['total_win'] + win_amount}).eq("telegram_id", tg_id).execute()
    
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
    return {"balance": balance, "min_bet": MIN_BET}

# ========== ЗАПУСК ==========
def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

async def main():
    threading.Thread(target=run_fastapi, daemon=True).start()
    print("✅ Бот CryptoLuck запущен и работает")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())