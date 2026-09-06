FROM python:3.9-slim
WORKDIR /app
COPY . /app
EXPOSE 8485 9333
CMD ["python", "node_cli.py"]
