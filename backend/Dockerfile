FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
COPY sdk ./sdk
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir ./sdk

COPY backend/app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
