FROM python:3.12-slim
RUN apt-get update && apt-get install -y \
  curl \
  build-essential \
  libffi-dev \
  && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"
WORKDIR /app
COPY . .
RUN uv sync --locked --no-dev
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]
