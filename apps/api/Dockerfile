FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
    libffi-dev shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Chromium + dependencias de sistema (libnss3, etc.) para Playwright en imagen slim
RUN playwright install --with-deps chromium

COPY . .

ENV DATA_DIR=/data
EXPOSE 8000

# Production entrypoint (no --reload). Dev hot-reload: docker-compose.dev.yml overrides command.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
