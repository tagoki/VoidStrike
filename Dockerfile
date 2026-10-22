# Базовый легковесный образ Python
FROM python:3.11-slim

# Отключаем буферизацию вывода Python и создание .pyc файлов
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения и точку входа
COPY app/ ./app/
COPY void_strike.py .

# Создаем директорию для отчетов
RUN mkdir -p /app/reports

# Точка входа для запуска интерактивного CLI
ENTRYPOINT ["python", "void_strike.py"]
