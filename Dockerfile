FROM docker.io/library/python:3.10-slim@sha256:5f9928ea39771e8ddf4fb9a96ab24f65f087793635614405a1dc9384f040852e

# 1. Install heavy system level runtimes required for audio analysis (sndfile) and computer vision (GL/Mesa)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 2. Configure system user space mappings for compliance
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# 3. Pre-initialize and permission-lock all biometric binary directories
RUN mkdir -p fingerprints faces face_embeddings voices voice_signatures uploads && \
    chown -R user:user /home/user/app

# 4. Drop downstream process runtime into user execution context
USER user

# 5. Populate and build python binary packages inside local cache architectures
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 6. Pre-seed deep learning weight cache directory pathways for models (Facenet/DeepFace compatibility)
RUN mkdir -p /home/user/.deepface/weights

# 7. Bridge local application path binary environments
ENV PATH="/home/user/.local/bin:${PATH}"

# 8. Import codebase source structures
COPY --chown=user:user . .

# 9. Bind execution pipeline onto Hugging Face Spaces designated port parameters
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]