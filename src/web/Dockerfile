FROM python:3.12-slim

WORKDIR /app

# System deps for pillow if it needs building; kept minimal
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY src/web/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy repo layout so 'src.web.main' and 'src.agent.*' both resolve
COPY src/ /app/src/
COPY data/ /app/data/

ENV PYTHONPATH=/app
ENV PORT=8080
ENV CONTOSO_VARIANT=baseline

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "src.web.main:app", "--host", "0.0.0.0", "--port", "8080"]
