from aiogram import types, Dispatcher
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import register_user, get_user
from config import MIN_BET, CRYPTO_WALLET, WEBAPP_URL

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Играть", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="💼 Кошелек", callback_data="wallet"), 
         InlineKeyboardButton(text="📊 Топ", callback_data="top")],
        [InlineKeyboardButton(text="👑 Проверить честность", callback_data="fair")]
    ])

async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or str(user_id)
    
    success = register_user(user_id, username)
    
    if success:
        await message.reply(
            f"🔥 Добро пожаловать в CryptoLuck, {username}!\n"
            f"💰 Мин. ставка: {MIN_BET} Stars\n"
            f"⚡️ Рейк: 10%\n"
            f"👇 Нажми 'Играть', чтобы начать!",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.reply("❌ Ошибка регистрации. Попробуйте позже.")

async def wallet_cmd(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id)
    balance = user['balance'] if user else 0
    await callback.message.answer(
        f"💵 *Твой баланс:* {balance} Stars\n\n"
        f"💳 *Пополнить баланс:*\n"
        f"Купи Stars через @wallet и напиши админу.\n"
        parse_mode="MARKDOWN"
    )
    await callback.answer()

async def top_cmd(callback: types.CallbackQuery):
    from supabase import create_client
    from config import SUPABASE_URL, SUPABASE_KEY
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    tops = supabase.table("users").select("username, balance").order("balance", desc=True).limit(10).execute()
    text = "🏆 *ТОП-10 ИГРОКОВ (Stars):*\n\n"
    for i, u in enumerate(tops.data, 1):
        text += f"{i}. {u['username']} — {u['balance']} Stars\n"
    await callback.message.answer(text, parse_mode="MARKDOWN")
    await callback.answer()

async def fair_cmd(callback: types.CallbackQuery):
    await callback.message.answer(
        "🔐 *Provably Fair*\n\n"
        "Каждый результат игры подписывается серверным хэшем.\n"
        "Проверить честность можно будет в следующей версии.",
        parse_mode="MARKDOWN"
    )
    await callback.answer()

def register_user_handlers(dp: Dispatcher):
    dp.message.register(start_cmd, Command("start"))
    dp.callback_query.register(wallet_cmd, lambda c: c.data == "wallet")
    dp.callback_query.register(top_cmd, lambda c: c.data == "top")
    dp.callback_query.register(fair_cmd, lambda c: c.data == "fair")
