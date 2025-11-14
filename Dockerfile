# Use official Python image
FROM python:3.12-slim

# Set workdir
WORKDIR /app

# Install system deps for Telethon (very lightweight)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements.txt /app/
COPY mastlinkbot.py /app/
COPY server.py /app/
COPY start.sh /app/


# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run script on container start
CMD ["bash", "start.sh"]
