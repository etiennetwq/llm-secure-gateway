FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN useradd --create-home gateway \
    && mkdir -p /app/data /app/exports \
    && chown -R gateway:gateway /app
USER gateway

EXPOSE 8000 8501
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
