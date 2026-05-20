from fastapi import APIRouter, Request
from database import get_user, update_balance
from game_logic import play_coinflip
from config import MIN_BET

# ЕДИНСТВЕННЫЙ router. БЕЗ создания нового app
router = APIRouter()

@router.post("/play")
async def play(request: Request):
    data = await request.json()
    tg_id = data.get("tg_id")
    bet = float(data.get("bet"))
    choice = data.get("choice")
    
    user = get_user(tg_id)
    if not user or user['balance'] < bet:
        return {"status": "error", "message": "❌ Не хватает Stars"}
    
    if bet < MIN_BET:
        return {"status": "error", "message": f"❌ Мин. ставка: {MIN_BET} Stars"}
    
    result = play_coinflip(bet, choice)
    if not result:
        return {"status": "error", "message": "❌ Ошибка игры"}
    
    new_balance = user['balance'] + result['amount']
    update_balance(tg_id, new_balance)
    
    return {
        "status": "success",
        "result": result['result'],
        "win": result['win'],
        "new_balance": new_balance,
        "message": f"{'✅ ПОБЕДА!' if result['win'] else '❌ ПРОИГРЫШ!'} {result['amount']} Stars",
        "mode": "bot"
    }

@router.get("/balance")
async def balance(tg_id: int):
    user = get_user(tg_id)
    return {
        "balance": user['balance'] if user else 0,
        "min_bet": MIN_BET,
        "currency": "Stars"
    }
