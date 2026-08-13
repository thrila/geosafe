FROM oven/bun:1.2 AS bun

FROM python:3.13-slim
COPY --from=bun /usr/local/bin/bun /usr/local/bin/bun
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY backend/pyproject.toml backend/pyproject.toml
RUN cd backend && uv sync --no-dev
COPY backend backend
COPY dji-flight-parser dji-flight-parser
WORKDIR /app/backend
ENV DB_PATH=/data/telemetry.db OUTPUT_DIR=/data/output UPLOAD_JOB_DIR=/data/upload_jobs
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
