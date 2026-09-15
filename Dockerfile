FROM alpine:3.22 AS builder
WORKDIR /build

RUN apk update \
    && apk upgrade \
    && apk add --no-cache python3 py3-pip \
    && rm -rf /var/cache/apk/*

COPY requirements-dee-security.txt /build/requirements-dee-security.txt

# Build the application Python environment from Alpine's own Python runtime.
# Build-time packaging tools are removed before the runtime image is assembled.
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/python -m pip install --no-cache-dir --upgrade -r /build/requirements-dee-security.txt \
    && /opt/venv/bin/python -m pip uninstall -y msgpack setuptools pip \
    && /opt/venv/bin/python -c "import cryptography, sqlalchemy, psycopg"

FROM alpine:3.22
WORKDIR /app

RUN apk update \
    && apk upgrade \
    && apk add --no-cache python3 ca-certificates tzdata libstdc++ libgcc \
    && rm -rf /var/cache/apk/*

COPY --from=builder /opt/venv /opt/venv
COPY . /app

RUN addgroup -S gerchain \
    && adduser -S -D -H -G gerchain gerchain \
    && chown -R gerchain:gerchain /app /opt/venv

USER gerchain

EXPOSE 8485 9333
CMD ["/opt/venv/bin/python", "node_cli.py"]
