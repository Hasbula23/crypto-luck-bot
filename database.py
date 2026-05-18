from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime
import traceback

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def register_user(tg_id, username):
    try:
        print(f"🔍 Начинаем регистрацию {tg_id}...")
        print(f"📡 URL: {SUPABASE_URL}")
        print(f"🔑 KEY: {SUPABASE_KEY[:20]}... (обрезано для безопасности)")
        
        # Проверяем подключение
        test = supabase.table("users").select("count").execute()
        print(f"✅ Подключение к Supabase работает. Тест: {test}")
        
        # Проверяем, есть ли пользователь
        user = supabase.table("users").select("*").eq("telegram_id", tg_id).execute()
        print(f"🔍 Поиск пользователя: {user.data}")
        
        if user.data:
            print(f"✅ Пользователь {tg_id} уже существует")
            return True
        
        # Вставляем нового
        data = {
            "telegram_id": tg_id,
            "username": username,
            "balance": 0,
            "total_bet": 0,
            "total_win": 0,
            "created_at": datetime.now().isoformat()
        }
        print(f"📝 Вставляем данные: {data}")
        
        result = supabase.table("users").insert(data).execute()
        print(f"✅ Результат вставки: {result}")
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА РЕГИСТРАЦИИ: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

def get_user(tg_id):
    try:
        user = supabase.table("users").select("*").eq("telegram_id", tg_id).execute()
        return user.data[0] if user.data else None
    except Exception as e:
        print(f"❌ Ошибка получения пользователя: {e}")
        return None

def update_balance(tg_id, new_balance):
    try:
        supabase.table("users").update({"balance": new_balance}).eq("telegram_id", tg_id).execute()
        return True
    except Exception as e:
        print(f"❌ Ошибка обновления баланса: {e}")
        return False
