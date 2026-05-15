import logging
from datetime import datetime

# Настраиваем красивое логирование в консоль Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def log_admin_action(action, user_id, result, details=""):
    """Любое действие админа пишем в консоль и можно будет слать в Telegram"""
    log_msg = f"ADMIN ACTION: {action} | UserID: {user_id} | Result: {result} | {details}"
    logger.info(log_msg)
    # Позже добавим сюда отправку в секретный чат