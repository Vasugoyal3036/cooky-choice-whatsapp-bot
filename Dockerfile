# Multi-stage build: copy Node.js directly into official Python 3.12 (Zero apt mirror errors)
FROM node:20-bookworm-slim AS node_base

FROM python:3.12-slim-bookworm

# Copy Node.js runtime and npm from node_base
COPY --from=node_base /usr/local/bin/node /usr/local/bin/node
COPY --from=node_base /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Node requirements for WhatsApp bridge
COPY whatsapp_bridge/package*.json ./whatsapp_bridge/
WORKDIR /app/whatsapp_bridge
RUN npm install --ignore-scripts

# Copy application files
WORKDIR /app
COPY . .

ENV PORT=8000
ENV HOST=0.0.0.0
EXPOSE 8000

CMD ["python", "main.py"]
