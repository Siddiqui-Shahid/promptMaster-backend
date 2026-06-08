FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FIREBASE_PROJECT_ID=asdasdasdasdasdasdertghrh

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY main.py ./
COPY docker/entrypoint.sh /entrypoint.sh

ENV PYTHONPATH=/app
RUN chmod +x /entrypoint.sh \
    && adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app /entrypoint.sh

USER appuser

EXPOSE 8000

CMD ["/entrypoint.sh"]
