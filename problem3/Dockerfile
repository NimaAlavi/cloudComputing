FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY server.py .

EXPOSE 8000

CMD ["python", "server.py"]