FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/
ENV BOT_TOKEN="TEST_TOKEN"

CMD [ "python", "main.py" ]
