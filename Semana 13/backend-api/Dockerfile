FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend_api.py .
EXPOSE 9000
CMD ["uvicorn", "backend_api:app", "--host", "0.0.0.0", "--port", "9000"]
