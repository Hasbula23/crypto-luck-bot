from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def register_user(tg_id, username):
    try:
        # Проверяем, есть ли уже
        user = supabase.table("users").select("*").eq("telegram_id", tg_id).execute()
        if user.data:
            return True
        # Вставляем нового
        supabase.table("users").insert({
            "telegram_id": tg_id,
            "username": username,
            "balance": 0,
            "total_bet": 0,
            "total_win": 0,
            "created_at": datetime.now().isoformat()
        }).execute()
        print(f"✅ Пользователь {tg_id} зарегистрирован")
        return True
    except Exception as e:
        print(f"❌ Ошибка регистрации {tg_id}: {e}")
        return False

def get_user(tg_id):
    try:
        user = supabase.table("users").select("*").eq("telegram_id", tg_id).execute()
        return user.data[0] if user.data else None
    except:
        return None

def update_balance(tg_id, new_balance):
    try:
        supabase.table("users").update({"balance": new_balance}).eq("telegram_id", tg_id).execute()
        return True
    except:
        return False
