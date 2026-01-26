FROM python:3.11-slim

# set workdirectory
WORKDIR /app

# install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy application code
COPY . .

# Open ports for flask
EXPOSE 5000

# 
CMD ["gunicorn", "--workers", "1", "--bind", "0.0.0.0:5000", "backend.app:app"]

