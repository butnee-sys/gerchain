FROM python:3.13-alpine3.22
WORKDIR /app

RUN apk update \
    && apk upgrade \
    && rm -rf /var/cache/apk/*

COPY . /app

# Install the current remediated Python package versions. The resolver may
# select a newer safe msgpack release than the minimum declared requirement.
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir --force-reinstall --no-deps 'msgpack==1.2.2' 'setuptools==83.0.0' \
    && python -m pip install --no-cache-dir --upgrade -r requirements-dee-security.txt \
    && python -c "from importlib.metadata import version; assert version('msgpack') == '1.2.2'; assert version('setuptools') == '83.0.0'"

RUN addgroup -S gerchain \
    && adduser -S -D -H -G gerchain gerchain \
    && chown -R gerchain:gerchain /app

USER gerchain

EXPOSE 8485 9333
CMD ["python", "node_cli.py"]
