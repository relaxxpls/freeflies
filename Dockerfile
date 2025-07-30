# FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime
FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy application code
COPY . .

RUN ./scripts/install.sh

# # Make entrypoint executable
# RUN chmod +x scripts/entrypoint.sh

# Expose port for Streamlit
EXPOSE 8501

# Use custom entrypoint
ENTRYPOINT ["scripts/entrypoint.sh"]
