FROM python:3.13-slim
ARG VERSION=dev
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY src /app/src
COPY static /app/static
VOLUME /data
ENV CASHCOMPASS_DB_PATH=/data/cashcompass.db
ENV CASHCOMPASS_PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "python -m uvicorn src.main:app --host 0.0.0.0 --port ${CASHCOMPASS_PORT:-8080} --no-access-log"]
