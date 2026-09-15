FROM python:3.13-slim
WORKDIR /app

# Refresh the Debian base packages before installing application dependencies.
# This is a CORE container-security control; SHUUD images are out of scope.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# Install the CORE security/runtime dependencies in the container itself.
# This includes Ed25519 cryptography plus the PostgreSQL/SQLAlchemy stack
# used by the governed release path.
RUN pip install --no-cache-dir -r requirements-dee-security.txt \
    && groupadd --system gerchain \
    && useradd --system --gid gerchain --home-dir /app --no-create-home gerchain \
    && chown -R gerchain:gerchain /app

USER gerchain

EXPOSE 8485 9333
CMD ["python", "node_cli.py"]
