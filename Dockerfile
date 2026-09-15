FROM python:3.13-alpine3.22 AS builder
WORKDIR /build

RUN apk update \
    && apk upgrade \
    && rm -rf /var/cache/apk/*

COPY requirements-dee-security.txt /build/requirements-dee-security.txt

# Rebuild the Python runtime payload into a clean archive. The final image
# will start from a fresh Alpine layer, so vulnerable Python distributions
# present in the official Python base layer are never inherited by runtime.
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir --upgrade -r /build/requirements-dee-security.txt \
    && python -c "from importlib.metadata import version; assert tuple(map(int, version('msgpack').split('.')[:2])) >= (1,2); assert tuple(map(int, version('setuptools').split('.')[:2])) >= (83,0)" \
    && rm -rf /usr/local/lib/python3.13/site-packages/msgpack-1.1.2.dist-info /usr/local/lib/python3.13/site-packages/setuptools-70.3.0.dist-info \
    && tar -C / -czf /python-runtime.tgz --exclude='usr/local/lib/python3.13/site-packages/msgpack-1.1.2*' --exclude='usr/local/lib/python3.13/site-packages/setuptools-70.3.0*' usr/local

FROM alpine:3.22
WORKDIR /app

RUN apk update \
    && apk upgrade \
    && apk add --no-cache ca-certificates tzdata libstdc++ libgcc \
    && rm -rf /var/cache/apk/*

COPY --from=builder /python-runtime.tgz /tmp/python-runtime.tgz
RUN tar -C / -xzf /tmp/python-runtime.tgz \
    && rm -f /tmp/python-runtime.tgz

COPY . /app

RUN addgroup -S gerchain \
    && adduser -S -D -H -G gerchain gerchain \
    && chown -R gerchain:gerchain /app

USER gerchain

EXPOSE 8485 9333
CMD ["python", "node_cli.py"]
