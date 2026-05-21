from aiogram import types, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import get_user, update_balance
from config import ADMIN_ID, CASINO_BANK

# ==================== АДМИН-КЛАВИАТУРА ====================
admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Пополнить баланс"), KeyboardButton(text="💰 Баланс игрока")],
        [KeyboardButton(text="📋 Все игроки"), KeyboardButton(text="💸 Вывести Stars")],
        [KeyboardButton(text="🏦 Банк казино"), KeyboardButton(text="💼 Моя зарплата")],
        [KeyboardButton(text="🔙 Выйти из админки")]
    ],
    resize_keyboard=True
)

# ==================== ВХОД В АДМИНКУ ====================
async def secret_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ Нет доступа")
        return
    await message.reply("🛡 *Админ-панель CryptoLuck*", reply_markup=admin_kb, parse_mode="Markdown")

# ==================== ПОПОЛНЕНИЕ БАЛАНСА (ручное) ====================
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
            await message.reply(f"✅ Начислено {amount} Stars. Новый баланс: {new_bal}")
        else:
            await message.reply("❌ Пользователь не найден")
    except:
        await message.reply("❌ Ошибка. Формат: `ID СУММА`")

# ==================== ПРОСМОТР БАЛАНСА ИГРОКА ====================
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
            await message.reply(f"👤 {user['username']}\n💰 Баланс: {user['balance']} Stars")
        else:
            await message.reply("❌ Пользователь не найден")
    except:
        await message.reply("❌ Ошибка. ID должен быть числом.")

# ==================== СПИСОК ИГРОКОВ ====================
async def admin_list(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    from supabase import create_client
    from config import SUPABASE_URL, SUPABASE_KEY
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    users = supabase.table("users").select("username, balance").order("balance", desc=True).limit(20).execute()
    text = "📋 *Топ-20 игроков:*\n\n"
    for u in users.data:
        text += f"🔹 {u['username']} — {u['balance']} Stars\n"
    await message.reply(text, parse_mode="Markdown")

# ==================== ВЫВОД STARS (от 200) ====================
async def admin_withdraw_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.reply("💰 *Вывод Stars*\n\nВведи ID игрока и сумму (мин. 200 Stars):\nПример: `7955348018 500`", parse_mode="Markdown")

async def admin_withdraw_confirm(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            await message.reply("❌ Ошибка. Формат: `ID СУММА`")
            return
        user_id = int(parts[0])
        amount = int(parts[1])
        
        if amount < 200:
            await message.reply("❌ Минимальный вывод: 200 Stars")
            return
        
        user = get_user(user_id)
        if not user or user['balance'] < amount:
            await message.reply("❌ У игрока недостаточно Stars")
            return
        
        # Списание с баланса игрока
        new_balance = user['balance'] - amount
        update_balance(user_id, new_balance)
        
        # Инструкция для отправки Stars
        await message.reply(
            f"✅ *Списано {amount} Stars* с баланса игрока {user_id}\n"
            f"👤 Игрок: {user['username']}\n"
            f"💰 Остаток: {new_balance} Stars\n\n"
            f"📤 *Отправь Stars вручную:*\n"
            f"1. Открой @wallet\n"
            f"2. Нажми 'Отправить'\n"
            f"3. Введи ID или юзернейм игрока: `{user_id}`\n"
            f"4. Укажи сумму: `{amount}` Stars\n"
            f"5. Подтверди перевод\n\n"
            f"⚠️ Комиссия Telegram: ~5% (вычти из суммы, если хочешь)",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

# ==================== ИНФОРМАЦИЯ О БАНКЕ КАЗИНО ====================
async def admin_bank_info(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    # Здесь можно вычислить общий рейк из БД
    await message.reply(
        f"🏦 *Банк казино:* {CASINO_BANK} Stars\n"
        f"💰 *Твой доход (рейк):* {CASINO_BANK - 500} Stars\n"
        f"📈 *Комиссия с игроков:* 10%\n"
        f"🔒 *Защита банка:* авто-проигрыш при ставке > {CASINO_BANK * 0.5} Stars\n\n"
        f"🔧 *Чтобы вывести себе:* используй '💸 Вывести Stars' с твоего ID.",
        parse_mode="Markdown"
    )

# ==================== ТВОЯ ЗАРПЛАТА (отдельный кошелёк) ====================
async def admin_salary(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    # Получаем общий рейк (сумму всех выигрышей казино)
    from supabase import create_client
    from config import SUPABASE_URL, SUPABASE_KEY
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Сумма всех проигрышей игроков (твой доход)
    result = supabase.table("users").select("total_bet").execute()
    total_bet = sum(u['total_bet'] for u in result.data if u.get('total_bet'))
    
    # Рейк 10%
    your_profit = total_bet * 0.1
    
    await message.reply(
        f"💼 *Твоя зарплата (рейк с игроков)*\n\n"
        f"📊 Общий объём ставок: {total_bet} Stars\n"
        f"💰 Твой доход (10%): {your_profit} Stars\n"
        f"🏦 Банк казино: {CASINO_BANK} Stars\n\n"
        f"🔧 *Чтобы вывести:* используй '💸 Вывести Stars' с твоего ID",
        parse_mode="Markdown"
    )

# ==================== ВЫХОД ИЗ АДМИНКИ ====================
async def admin_exit(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.reply("🔒 Выход из админ-панели", reply_markup=types.ReplyKeyboardRemove())

# ==================== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ====================
def register_admin_handlers(dp: Dispatcher):
    dp.message.register(secret_admin, Command("cryptoluck_admin"))
    
    # Пополнение
    dp.message.register(admin_add_start, lambda m: m.text == "➕ Пополнить баланс" and m.from_user.id == ADMIN_ID)
    dp.message.register(admin_add_confirm, lambda m: m.text and m.text[0].isdigit() and len(m.text.split()) == 2 and m.from_user.id == ADMIN_ID)
    
    # Баланс игрока
    dp.message.register(admin_balance_start, lambda m: m.text == "💰 Баланс игрока" and m.from_user.id == ADMIN_ID)
    dp.message.register(admin_show_balance, lambda m: m.text.isdigit() and m.from_user.id == ADMIN_ID)
    
    # Список игроков
    dp.message.register(admin_list, lambda m: m.text == "📋 Все игроки" and m.from_user.id == ADMIN_ID)
    
    # Вывод Stars
    dp.message.register(admin_withdraw_start, lambda m: m.text == "💸 Вывести Stars" and m.from_user.id == ADMIN_ID)
    dp.message.register(admin_withdraw_confirm, lambda m: m.text and m.text[0].isdigit() and len(m.text.split()) == 2 and m.from_user.id == ADMIN_ID)
    
    # Банк казино и зарплата
    dp.message.register(admin_bank_info, lambda m: m.text == "🏦 Банк казино" and m.from_user.id == ADMIN_ID)
    dp.message.register(admin_salary, lambda m: m.text == "💼 Моя зарплата" and m.from_user.id == ADMIN_ID)
    
    # Выход
    dp.message.register(admin_exit, lambda m: m.text == "🔙 Выйти из админки" and m.from_user.id == ADMIN_ID)
