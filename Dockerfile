FROM python:3.13-slim
WORKDIR /app

# Refresh the Debian base packages before installing application dependencies.
# This is a CORE container-security control; SHUUD images are out of scope.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# Remove stale Python distribution metadata from the base image before
# installing the remediated packages. This prevents Trivy from reporting an
# obsolete package metadata record after the runtime package is upgraded.
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -c "import glob, shutil; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('/usr/local/lib/python*/site-packages/msgpack-*.dist-info') + glob.glob('/usr/local/lib/python*/site-packages/setuptools-*.dist-info')]" \
    && python -m pip install --no-cache-dir --ignore-installed 'msgpack>=1.2.1,<2' 'setuptools>=83.0.0,<84' \
    && python -m pip install --no-cache-dir --upgrade -r requirements-dee-security.txt \
    && python -c "import msgpack, setuptools; assert tuple(map(int, msgpack.__version__.split('.')[:2])) >= (1,2); assert tuple(map(int, setuptools.__version__.split('.')[:2])) >= (83,0)"

RUN groupadd --system gerchain \
    && useradd --system --gid gerchain --home-dir /app --no-create-home gerchain \
    && chown -R gerchain:gerchain /app

USER gerchain

EXPOSE 8485 9333
CMD ["python", "node_cli.py"]
