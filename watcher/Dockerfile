FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1
# Install docker-cli so we can run 'docker exec'
RUN apt-get update && apt-get install -y docker.io
RUN pip install watchdog
COPY watcher.py /app/watcher.py
WORKDIR /app
CMD ["python", "watcher.py"]
