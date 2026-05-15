from aiogram import types, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from database import get_user, update_balance
from config import ADMIN_ID

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Пополнить"), KeyboardButton(text="💰 Баланс")],
        [KeyboardButton(text="📋 Список"), KeyboardButton(text="🔙 Выход")]
    ],
    resize_keyboard=True
)

async def secret_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ Нет доступа")
        return
    await message.reply("🛡 Админка", reply_markup=admin_kb)

# ----- ИСПРАВЛЕННЫЕ ОБРАБОТЧИКИ -----
async def admin_add_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.reply("Введи: ID СУММА (например: 7955348018 100)")

async def admin_add_confirm(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            await message.reply("❌ Ошибка. Формат: `ID СУММА`")
            return
        user_id = int(parts[0])
        amount = float(parts[1])
        
        user = get_user(user_id)
        if user:
            new_bal = user['balance'] + amount
            update_balance(user_id, new_bal)
            await message.reply(f"✅ Начислено {amount} USDT. Баланс: {new_bal}")
        else:
            await message.reply("❌ Пользователь не найден")
    except ValueError:
        await message.reply("❌ Ошибка. ID должен быть числом, сумма — числом.")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {str(e)}")

async def admin_balance_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.reply("Введи ID игрока:")

async def admin_show_balance(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.strip())
        user = get_user(user_id)
        if user:
            await message.reply(f"👤 {user['username']}\n💰 {user['balance']} USDT")
        else:
            await message.reply("❌ Не найден")
    except:
        await message.reply("❌ Ошибка. ID должен быть числом.")

async def admin_list(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    from supabase import create_client
    from config import SUPABASE_URL, SUPABASE_KEY
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    users = supabase.table("users").select("username, balance").order("balance", desc=True).limit(20).execute()
    text = "📋 Топ-20:\n\n"
    for u in users.data:
        text += f"🔹 {u['username']} — {u['balance']} USDT\n"
    await message.reply(text)

async def admin_exit(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.reply("🔒 Выход", reply_markup=types.ReplyKeyboardRemove())

def register_admin_handlers(dp: Dispatcher):
    dp.message.register(secret_admin, Command("cryptoluck_admin"))
    dp.message.register(admin_add_start, lambda m: m.text == "➕ Пополнить" and m.from_user.id == ADMIN_ID)
    dp.message.register(admin_add_confirm, lambda m: m.text and m.text[0].isdigit() and m.from_user.id == ADMIN_ID)
    dp.message.register(admin_balance_start, lambda m: m.text == "💰 Баланс" and m.from_user.id == ADMIN_ID)
    dp.message.register(admin_show_balance, lambda m: m.text.isdigit() and m.from_user.id == ADMIN_ID)
    dp.message.register(admin_list, lambda m: m.text == "📋 Список" and m.from_user.id == ADMIN_ID)
    dp.message.register(admin_exit, lambda m: m.text == "🔙 Выход" and m.from_user.id == ADMIN_ID)