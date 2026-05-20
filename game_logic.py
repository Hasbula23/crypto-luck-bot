import random
from config import REK, MIN_BET, CASINO_BANK

def play_coinflip(bet, choice):
    # Проверка минимальной ставки
    if bet < MIN_BET:
        return None, f"Минимальная ставка: {MIN_BET} Stars"
    
    # === ЗАЩИТА БАНКА ===
    # Если ставка превышает 50% от банка казино — автоматический проигрыш
    if bet > CASINO_BANK * 0.5:
        result = "tails" if choice == "heads" else "heads"
        return {
            "result": result,
            "win": False,
            "amount": -bet,
            "message": f"❌ АВТОПРОИГРЫШ! Ставка {bet} Stars превышает лимит банка."
        }
    
    # === ЧЕСТНАЯ ИГРА ===
    # Шанс игрока 30%, казино 70%
    win = random.random() <= 0.3
    
    if win:
        # Выигрыш: (ставка × 1.5) − (ставка × рейк)
        win_amount = (bet * 1.5) - (bet * REK)
        result = choice  # Игрок угадал
        message = f"✅ ПОБЕДА! +{win_amount:.0f} Stars"
        return {
            "result": result,
            "win": True,
            "amount": win_amount,
            "message": message
        }
    else:
        # Проигрыш
        result = "tails" if choice == "heads" else "heads"
        message = f"❌ ПРОИГРЫШ! -{bet:.0f} Stars"
        return {
            "result": result,
            "win": False,
            "amount": -bet,
            "message": message
        }
