# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files (respects .dockerignore)
COPY . .

RUN echo "Content of /code:" && ls -la && echo "Content of /code/app:" && ls -la app/

EXPOSE 8080

CMD ["python", "startup.py"]
