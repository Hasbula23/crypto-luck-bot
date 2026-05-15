from fastapi import FastAPI, Request
from database import get_user, update_balance
from game_logic import play_coinflip

app = FastAPI()  # <-- ЭТА СТРОКА БЫЛА ПРОПУЩЕНА

@app.post("/api/play")
async def play(request: Request):
    data = await request.json()
    tg_id = data.get("tg_id")
    bet = float(data.get("bet"))
    choice = data.get("choice")
    
    user = get_user(tg_id)
    if not user or user['balance'] < bet:
        return {"status": "error", "message": "Не хватает средств"}
    
    result = play_coinflip(bet, choice)
    if not result:
        return {"status": "error", "message": "Минимальная ставка 5 USDT"}
    
    new_balance = user['balance'] + result['amount']
    update_balance(tg_id, new_balance)
    
    return {
        "status": "success",
        "result": result['result'],
        "win": result['win'],
        "new_balance": new_balance,
        "message": "Победа!" if result['win'] else "Проигрыш!"
    }

@app.get("/api/balance")
async def balance(tg_id: int):
    user = get_user(tg_id)
    return {"balance": user['balance'] if user else 0}