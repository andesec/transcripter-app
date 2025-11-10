# Dockerfile for the unified transcripter application
FROM python:3.9-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy requirements and install dependencies with uv
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy the application source code
COPY src/ ./src/

# Copy the .env file
COPY .env .

# Expose the ports for Streamlit and FastAPI
EXPOSE 8501
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "src.main"]
