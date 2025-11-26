# Dockerfile for DeepAgent Coding Assistant
FROM python:3.13-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY README.md ./
COPY config.example.yaml ./

# Install dependencies
RUN uv sync --frozen

# Expose port (if needed for future web interface)
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["uv", "run", "python", "-m", "deepagent_coder.main"]
CMD ["chat"]
