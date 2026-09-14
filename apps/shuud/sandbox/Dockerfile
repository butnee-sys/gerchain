FROM python:3.13-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY . /app

RUN pip install --no-cache-dir \
    "fastapi>=0.115,<1" \
    "uvicorn>=0.30,<1" \
    "sqlalchemy>=2,<3" \
    "psycopg[binary]>=3.2,<4" \
    "pydantic>=2,<3"

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "shuud.server:app", "--host", "0.0.0.0", "--port", "8000"]
