FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App + assets (IMPORTANTE: copiar templates e static)
COPY app.py .
COPY templates ./templates
COPY static ./static

EXPOSE 5050

# Produção com gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5050", "app:app"]
