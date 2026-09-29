FROM python:3.13-slim

WORKDIR /app

COPY src/web/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --requirement /tmp/requirements.txt

COPY src/ /app/src/
COPY data/fixtures/ /app/data/fixtures/

ENV PYTHONPATH=/app
ENV PORT=8080

EXPOSE 8080

RUN PYTHONDONTWRITEBYTECODE= python -m compileall -q /app/src/web

CMD ["python", "-m", "uvicorn", "src.web.main:app", "--host", "0.0.0.0", "--port", "8080"]
