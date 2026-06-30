# Base dynamic image with Python environment running
FROM python:3.10-slim

# Install system-level graphics and internal OS mapping pipelines
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Setup non-privilege isolated container user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Pre-verify storage dimensions caching setup
RUN mkdir -p fingerprints uploads

# Install assets components modules mapping
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Sync application source data
COPY --chown=user:user . .

# Open dynamic port mapping for Streamlit container execution context
EXPOSE 7860

# Launch application orchestration via default endpoint parameters mapping
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]