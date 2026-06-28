# Stage 1: Build dependencies
FROM python:3.11-bookworm AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1



COPY requirements.txt .
RUN pip install \
    --default-timeout=1000 \
    --retries=10 \
    --no-cache-dir \
    --user \
    -r requirements.txt
# Stage 2: Final minimal image
FROM python:3.11-bookworm AS runner

WORKDIR /app

# Create a non-root security user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10000 -g appgroup -m -s /bin/bash appuser

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appgroup . .

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

USER appuser

# Launch via production server Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
