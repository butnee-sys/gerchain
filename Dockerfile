FROM alpine:3.22 AS builder
WORKDIR /build

RUN apk update \
    && apk upgrade \
    && apk add --no-cache python3 py3-pip python3-dev gcc musl-dev libffi-dev openssl-dev cargo \
    && rm -rf /var/cache/apk/*

COPY requirements-dee-security.txt /build/requirements-dee-security.txt

# Build a clean Python virtual environment from the Alpine Python package
# rather than inheriting the vulnerable Python distribution metadata from the
# official python image layer.
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/python -m pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/python -m pip install --no-cache-dir --upgrade -r /build/requirements-dee-security.txt \
    && /opt/venv/bin/python -c "from importlib.metadata import version; assert tuple(map(int, version('msgpack').split('.')[:2])) >= (1,2); assert tuple(map(int, version('setuptools').split('.')[:2])) >= (83,0)"

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

ENV PATH="/opt/venv/bin:$PATH"
USER gerchain

EXPOSE 8485 9333
CMD ["python", "node_cli.py"]
