FROM python:3.13-slim

WORKDIR /app/user_agent

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --requirement requirements.txt

COPY . ./

EXPOSE 8088

RUN PYTHONDONTWRITEBYTECODE= python -m compileall -q .

CMD ["python", "main.py"]
