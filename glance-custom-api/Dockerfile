FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy only the files needed for dependency installation
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --locked --no-install-project --no-dev

# Copy the rest of the application
COPY . .

# Install the project
RUN uv sync --locked --no-dev

# Set the PATH to include the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]