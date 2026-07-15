FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY requirements.txt ./
RUN python -m venv "$VIRTUAL_ENV" \
    && "$VIRTUAL_ENV/bin/python" -m pip install --no-cache-dir --upgrade pip \
    && "$VIRTUAL_ENV/bin/python" -m pip install --no-cache-dir -r requirements.txt

COPY app.py ./

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 3333

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD ["/opt/venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3333/healthz')"]

CMD ["/opt/venv/bin/python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3333"]
