# PM Claude orchestrator (optional for production)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-pm-claude.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-pm-claude.txt

# Copy PM Claude code
COPY src/ ./src/
COPY pm-* ./
COPY config/ ./config/

# Make scripts executable
RUN chmod +x pm-*

# Create non-root user
RUN useradd -m -u 1000 pmclaude && chown -R pmclaude:pmclaude /app
USER pmclaude

# This container can run various PM Claude commands
# e.g., docker run pmclaude ./pm-issue list
CMD ["./pm-claude", "status"]