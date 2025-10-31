FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install ChromaDB backend (most commonly used)
RUN pip install --no-cache-dir chromadb>=0.4.0

# Install chatbot dependencies
RUN pip install --no-cache-dir flask llama-cpp-python

# Copy the application code
COPY . .

# Add the app directory to Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Create directory for ChromaDB persistence
RUN mkdir -p /app/chroma_db

# Expose port if needed (for API endpoints)
EXPOSE 5001

# Default command - can be overridden
CMD ["python", "-c", "from cortex.core.yaml_memory_manager import YAMLMemoryManager; print('Cortex SDK is ready!')"]

