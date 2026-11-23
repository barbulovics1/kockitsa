# Slika aplikacije za namestitev; backend streže tudi frontend
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend backend
COPY frontend frontend
COPY db db
COPY seed seed

# Render nastavi vrata v spremenljivki PORT
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'"]
