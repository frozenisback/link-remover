#!/bin/sh
echo "Starting Telethon Link Remover Bot..."
python3 mastlinkbot.py &

echo "Starting  HTTP Server..."
python3 server.py &

# keep container alive
wait

