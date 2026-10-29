FROM node:20-bullseye-slim

# Install Python 3.12 and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy python dependencies and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy whatsapp_bridge and install npm dependencies
COPY whatsapp_bridge/package*.json ./whatsapp_bridge/
WORKDIR /app/whatsapp_bridge
RUN npm install --ignore-scripts

# Return to root and copy remaining files
WORKDIR /app
COPY . .

# Environment variables
ENV PORT=8000
ENV HOST=0.0.0.0
EXPOSE 8000

# Start server
CMD ["python3", "main.py"]
