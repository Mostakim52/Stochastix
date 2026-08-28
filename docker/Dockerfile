FROM python:3.13-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install ".[api]" || pip install --no-cache-dir --prefix=/install .

FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STOCKFORGE_LOG_LEVEL=INFO

RUN useradd --create-home --shell /bin/bash forge
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --from=builder /build/src /app/src
COPY configs /app/configs

USER forge
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status==200 else 1)"

CMD ["uvicorn", "stockforge.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
