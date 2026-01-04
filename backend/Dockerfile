FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install with extended timeout
RUN pip install --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install Python dependencies with extended timeout and retries
RUN pip install --no-cache-dir \
    --default-timeout=1000 \
    --retries 5 \
    -r requirements.txt

# Copy application files
COPY . .

# Create uploads directory
RUN mkdir -p uploads/user_photos logs

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app_mongodb.py"]
