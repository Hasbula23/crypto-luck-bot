# Используем официальный образ Python 3.11
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем ВСЕ файлы из репозитория в текущую папку контейнера
COPY . .

# Устанавливаем зависимости Python из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт 8000 (для FastAPI)
EXPOSE 8000

# Запускаем бота
CMD ["python", "main.py"]