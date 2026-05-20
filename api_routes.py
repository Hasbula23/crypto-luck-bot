from fastapi import APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from database import get_user, update_balance
from game_logic import play_coinflip
from config import MIN_BET, REK, CASINO_BANK

router = APIRouter()

@router.post("/play")
async def play(request: Request):
    data = await request.json()
    tg_id = data.get("tg_id")
    bet = float(data.get("bet"))
    choice = data.get("choice")
    
    # Проверка наличия пользователя
    user = get_user(tg_id)
    if not user:
        return {"status": "error", "message": "❌ Пользователь не найден. Напишите /start в боте."}
    
    # Проверка достаточности средств
    if user['balance'] < bet:
        return {"status": "error", "message": f"❌ Не хватает Stars. Баланс: {user['balance']} Stars"}
    
    # Проверка минимальной ставки
    if bet < MIN_BET:
        return {"status": "error", "message": f"❌ Минимальная ставка: {MIN_BET} Stars"}
    
    # === ЗАЩИТА БАНКА КАЗИНО ===
    if bet > CASINO_BANK * 0.5:
        # Автоматический проигрыш
        new_balance = user['balance'] - bet
        update_balance(tg_id, new_balance)
        return {
            "status": "success",
            "result": "tails" if choice == "heads" else "heads",
            "win": False,
            "new_balance": new_balance,
            "message": f"❌ АВТОПРОИГРЫШ! Ставка {bet:.0f} Stars превышает лимит банка казино.",
            "mode": "bot"
        }
    
    # === ЧЕСТНАЯ ИГРА ===
    result_data = play_coinflip(bet, choice)
    if not result_data:
        return {"status": "error", "message": "❌ Ошибка игры"}
    
    # Обновляем баланс
    new_balance = user['balance'] + result_data['amount']
    update_balance(tg_id, new_balance)
    
    return {
        "status": "success",
        "result": result_data['result'],
        "win": result_data['win'],
        "new_balance": new_balance,
        "message": result_data['message'],
        "mode": "bot"
    }

@router.get("/balance")
async def balance(tg_id: int):
    user = get_user(tg_id)
    if not user:
        return {"balance": 0, "min_bet": MIN_BET, "currency": "Stars", "error": "User not found"}
    
    return {
        "balance": user['balance'],
        "min_bet": MIN_BET,
        "currency": "Stars"
    }

@router.get("/casino/bank")
async def casino_bank():
    """Возвращает текущий банк казино (для информации)"""
    return {
        "bank": CASINO_BANK,
        "max_fair_bet": CASINO_BANK * 0.5,
        "currency": "Stars"
    }
