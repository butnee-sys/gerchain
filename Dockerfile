FROM python:3.13-alpine3.22
WORKDIR /app

RUN apk update \
    && apk upgrade \
    && rm -rf /var/cache/apk/*

COPY . /app

# Remove any Python package files/metadata inherited from the base image,
# then install exact remediated versions. This prevents layer scanners from
# retaining obsolete distribution records.
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -c "import glob, shutil; paths=[]; paths += glob.glob('/usr/local/lib/python*/site-packages/msgpack'); paths += glob.glob('/usr/local/lib/python*/site-packages/msgpack-*.dist-info'); paths += glob.glob('/usr/local/lib/python*/site-packages/setuptools'); paths += glob.glob('/usr/local/lib/python*/site-packages/setuptools-*.dist-info'); [shutil.rmtree(p, ignore_errors=True) for p in paths]" \
    && python -m pip install --no-cache-dir --force-reinstall --no-deps 'msgpack==1.2.1' 'setuptools==83.0.0' \
    && python -m pip install --no-cache-dir --upgrade -r requirements-dee-security.txt \
    && python -c "from importlib.metadata import version; assert version('msgpack') == '1.2.1'; assert version('setuptools') == '83.0.0'"

RUN addgroup -S gerchain \
    && adduser -S -D -H -G gerchain gerchain \
    && chown -R gerchain:gerchain /app

USER gerchain

EXPOSE 8485 9333
CMD ["python", "node_cli.py"]
