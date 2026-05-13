# Используем официальный образ Python 3.11
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY requirements.txt .
COPY main.py .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт (Render требует, но не критично)
EXPOSE 8000

# Команда для запуска (включает FastAPI + бота)
CMD ["python", "main.py"]