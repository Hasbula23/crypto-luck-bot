from fastapi import FastAPI, Request
from database import get_user, update_balance
import random
import string
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, REK, MIN_BET

app = FastAPI()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== БОТ-КАЗИНО (30% на игрока, 70% на бота) ====================
@app.post("/api/play")
async def play_vs_bot(request: Request):
    data = await request.json()
    tg_id = data.get("tg_id")
    bet = float(data.get("bet"))
    
    if bet < MIN_BET:
        return {"status": "error", "message": f"Мин. ставка {MIN_BET} Stars"}
    
    user = get_user(tg_id)
    if not user or user['balance'] < bet:
        return {"status": "error", "message": "Не хватает средств"}
    
    # Шанс выигрыша 30% (игрок), 70% (бот)
    win = random.random() <= 0.3
    
    if win:
        # Выплата с учётом рейка (рейк 10% от выигрыша)
        payout = bet * 1.5 - (bet * REK)
        new_balance = user['balance'] + payout
        result_msg = f"✅ ПОБЕДА! +{payout:.2f} Stars"
    else:
        new_balance = user['balance'] - bet
        result_msg = f"❌ ПРОИГРЫШ! -{bet:.2f} Stars"
    
    update_balance(tg_id, new_balance)
    
    return {
        "status": "success",
        "win": win,
        "new_balance": new_balance,
        "message": result_msg,
        "mode": "bot"
    }

# ==================== PVP-РЕЖИМ (50/50) ====================
def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.post("/api/pvp/create")
async def create_pvp_room(request: Request):
    data = await request.json()
    tg_id = data.get("tg_id")
    bet = float(data.get("bet"))
    
    if bet < MIN_BET:
        return {"status": "error", "message": f"Мин. ставка {MIN_BET} Stars"}
    
    user = get_user(tg_id)
    if not user or user['balance'] < bet:
        return {"status": "error", "message": "Не хватает средств"}
    
    # Блокируем ставку (временно списываем)
    update_balance(tg_id, user['balance'] - bet)
    
    room_code = generate_room_code()
    
    supabase.table("pvp_rooms").insert({
        "room_code": room_code,
        "creator_id": tg_id,
        "creator_bet": bet,
        "status": "waiting"
    }).execute()
    
    return {
        "status": "success",
        "room_code": room_code,
        "bet": bet
    }

@app.post("/api/pvp/join")
async def join_pvp_room(request: Request):
    data = await request.json()
    tg_id = data.get("tg_id")
    room_code = data.get("room_code")
    
    # Находим комнату
    room = supabase.table("pvp_rooms").select("*").eq("room_code", room_code).eq("status", "waiting").execute()
    if not room.data:
        return {"status": "error", "message": "Комната не найдена или уже занята"}
    
    room = room.data[0]
    bet = room['creator_bet']
    
    user = get_user(tg_id)
    if not user or user['balance'] < bet:
        return {"status": "error", "message": f"Не хватает {bet} Stars для присоединения"}
    
    # Блокируем ставку второго игрока
    update_balance(tg_id, user['balance'] - bet)
    
    # Обновляем комнату
    supabase.table("pvp_rooms").update({
        "joiner_id": tg_id,
        "joiner_bet": bet,
        "status": "full"
    }).eq("room_code", room_code).execute()
    
    return {
        "status": "success",
        "room_code": room_code,
        "bet": bet
    }

@app.post("/api/pvp/play")
async def play_pvp(request: Request):
    data = await request.json()
    room_code = data.get("room_code")
    tg_id = data.get("tg_id")
    
    # Находим комнату
    room = supabase.table("pvp_rooms").select("*").eq("room_code", room_code).eq("status", "full").execute()
    if not room.data:
        return {"status": "error", "message": "Комната не готова к игре"}
    
    room = room.data[0]
    
    # Проверяем, что игрок участвует в игре
    if tg_id not in [room['creator_id'], room.get('joiner_id')]:
        return {"status": "error", "message": "Вы не участник этой игры"}
    
    # Честный рандом 50/50
    winner_id = random.choice([room['creator_id'], room['joiner_id']])
    bet = room['creator_bet']
    
    # Выплата победителю (ставка * 2 - рейк 10%)
    payout = bet * 2 - (bet * REK * 2)  # Рейк с обеих ставок
    winner = get_user(winner_id)
    if winner:
        update_balance(winner_id, winner['balance'] + payout)
    
    # Обновляем статус комнаты
    supabase.table("pvp_rooms").update({
        "status": "finished",
        "winner_id": winner_id
    }).eq("room_code", room_code).execute()
    
    return {
        "status": "success",
        "winner_id": winner_id,
        "payout": payout,
        "message": f"Победитель: {'Вы' if winner_id == tg_id else 'Соперник'}"
    }

@app.get("/api/balance")
async def get_balance(tg_id: int):
    user = get_user(tg_id)
    return {"balance": user['balance'] if user else 0, "min_bet": MIN_BET}
