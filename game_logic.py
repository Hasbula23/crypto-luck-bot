import random
from config import REK, MIN_BET

def play_coinflip(bet, choice):
    if bet < MIN_BET:
        return None, "Минимальная ставка"
    result = random.choice(["heads", "tails"])
    win = (result == choice)
    if win:
        win_amount = bet - (bet * REK)
        return {"result": result, "win": True, "amount": win_amount}
    else:
        return {"result": result, "win": False, "amount": -bet}