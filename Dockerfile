FROM python:3.13-slim
WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# Remove the Python packages bundled in the base image at the filesystem level
# before reinstalling remediated versions. This creates overlay whiteouts for
# both package code and distribution metadata so layer scanners cannot retain
# obsolete versions from the base layer.
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -c "import glob, shutil; paths=[]; paths += glob.glob('/usr/local/lib/python*/site-packages/msgpack'); paths += glob.glob('/usr/local/lib/python*/site-packages/msgpack-*.dist-info'); paths += glob.glob('/usr/local/lib/python*/site-packages/setuptools'); paths += glob.glob('/usr/local/lib/python*/site-packages/setuptools-*.dist-info'); [shutil.rmtree(p, ignore_errors=True) for p in paths]" \
    && python -m pip install --no-cache-dir --ignore-installed 'msgpack>=1.2.1,<2' 'setuptools>=83.0.0,<84' \
    && python -m pip install --no-cache-dir --upgrade -r requirements-dee-security.txt \
    && python -c "import msgpack, setuptools; assert tuple(map(int, msgpack.__version__.split('.')[:2])) >= (1,2); assert tuple(map(int, setuptools.__version__.split('.')[:2])) >= (83,0)"

RUN groupadd --system gerchain \
    && useradd --system --gid gerchain --home-dir /app --no-create-home gerchain \
    && chown -R gerchain:gerchain /app

USER gerchain

EXPOSE 8485 9333
CMD ["python", "node_cli.py"]
