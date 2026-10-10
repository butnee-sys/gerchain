FROM python:3.13-slim
WORKDIR /app

COPY . /app

# Install the DEE security/runtime dependencies in the container itself.
# This includes Ed25519 cryptography plus the PostgreSQL/SQLAlchemy stack
# used by the sandbox and governed release path.
RUN pip install --no-cache-dir -r requirements-dee-security.txt

# This image currently runs the canonical PostgreSQL runtime worker only.
# It does not start an HTTP/P2P listener, so no ports are published.
CMD ["python", "production_entrypoint.py"]
