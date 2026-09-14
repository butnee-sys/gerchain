FROM python:3.9-slim
WORKDIR /app

COPY . /app

# DEE security uses Ed25519 signing and verification from the cryptography package.
# Keep the runtime image self-contained so SHUUD/DEE sandbox startup does not
# depend on packages installed only in a developer environment.
RUN pip install --no-cache-dir cryptography

EXPOSE 8485 9333
CMD ["python", "node_cli.py"]
