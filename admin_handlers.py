from aiogram import types, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from database import get_user, update_balance
from config import ADMIN_ID
from logger import log_admin_action

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
        log_admin_action("ACCESS_DENIED", message.from_user.id, "FAIL", "Попытка входа в админку")
        return
    await message.reply("🛡 Админка", reply_markup=admin_kb)
    log_admin_action("ADMIN_ENTER", message.from_user.id, "SUCCESS")

async def admin_add_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.reply("Введи: ID СУММА (например: 7955348018 100)")

async def admin_add_confirm(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Жёсткое логирование того, что пришло
    raw_text = message.text
    user_id_for_log = message.from_user.id
    log_admin_action("RAW_INPUT", user_id_for_log, "RECEIVED", f"Текст: '{raw_text}' | Длина: {len(raw_text)}")
    
    try:
        # Убираем все возможные лишние символы (смайлы, пробелы в начале/конце)
        clean_text = raw_text.strip()
        # Проверяем, есть ли пробел
        if ' ' not in clean_text:
            await message.reply("❌ Ошибка: Нужно ввести ID и сумму через пробел")
            log_admin_action("ADD_BALANCE", user_id_for_log, "FAIL", "Нет пробела")
            return
            
        parts = clean_text.split()
        if len(parts) != 2:
            await message.reply("❌ Ошибка: Введи ровно два числа: ID и сумму")
            log_admin_action("ADD_BALANCE", user_id_for_log, "FAIL", f"Количество частей: {len(parts)}")
            return
        
        user_id = int(parts[0])
        amount = float(parts[1])
        
        if amount <= 0:
            await message.reply("❌ Ошибка: Сумма должна быть больше 0")
            return
            
        user = get_user(user_id)
        if not user:
            await message.reply(f"❌ Пользователь с ID {user_id} не найден в базе")
            log_admin_action("ADD_BALANCE", user_id_for_log, "FAIL", f"User {user_id} not found")
            return
            
        new_bal = user['balance'] + amount
        update_balance(user_id, new_bal)
        await message.reply(f"✅ Начислено {amount} USDT пользователю {user_id}\n💰 Новый баланс: {new_bal} USDT")
        log_admin_action("ADD_BALANCE", user_id_for_log, "SUCCESS", f"User {user_id} +{amount}")
        
    except ValueError as e:
        await message.reply("❌ Ошибка: ID должен быть целым числом, сумма - числом (можно с точкой)")
        log_admin_action("ADD_BALANCE", user_id_for_log, "FAIL", f"ValueError: {e}")
    except Exception as e:
        await message.reply(f"❌ Неизвестная ошибка: {str(e)}")
        log_admin_action("ADD_BALANCE", user_id_for_log, "FAIL", f"Exception: {e}")

# Остальные функции (admin_balance_start, admin_show_balance, admin_list, admin_exit, register_admin_handlers)
# остаются такими же, как в предыдущем сообщении (только добавь в них вызовы log_admin_action при ошибках/успехе)

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
    dp.message.register(admin_add_confirm, lambda m: m.text and m.from_user.id == ADMIN_ID)  # УБРАЛ isdigit()
    dp.message.register(admin_balance_start, lambda m: m.text == "💰 Баланс" and m.from_user.id == ADMIN_ID)
    dp.message.register(admin_show_balance, lambda m: m.text.isdigit() and m.from_user.id == ADMIN_ID)
    dp.message.register(admin_list, lambda m: m.text == "📋 Список" and m.from_user.id == ADMIN_ID)
    dp.message.register(admin_exit, lambda m: m.text == "🔙 Выход" and m.from_user.id == ADMIN_ID)