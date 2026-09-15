FROM python:3.13-alpine3.22
WORKDIR /app

RUN apk update \
    && apk upgrade \
    && rm -rf /var/cache/apk/*

COPY . /app

# Keep the CORE runtime on a current stable Alpine base and explicitly install
# the remediated Python dependencies. SHUUD images remain out of scope.
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir --upgrade -r requirements-dee-security.txt \
    && python -c "import msgpack, setuptools; assert tuple(map(int, msgpack.__version__.split('.')[:2])) >= (1,2); assert tuple(map(int, setuptools.__version__.split('.')[:2])) >= (83,0)"

RUN addgroup -S gerchain \
    && adduser -S -D -H -G gerchain gerchain \
    && chown -R gerchain:gerchain /app

USER gerchain

EXPOSE 8485 9333
CMD ["python", "node_cli.py"]
