FROM python:3.9-slim
WORKDIR /app

COPY . /app

# Install the DEE security/runtime dependencies in the container itself.
# This includes Ed25519 cryptography plus the PostgreSQL/SQLAlchemy stack
# used by the sandbox and governed release path.
RUN pip install --no-cache-dir -r requirements-dee-security.txt

EXPOSE 8485 9333
CMD ["python", "production_entrypoint.py"]
