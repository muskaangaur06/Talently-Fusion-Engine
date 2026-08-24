FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Render's Docker build context is the git repo itself, so the LFS-tracked binaries
# (jobs.db, jobs.faiss, the ONNX model) exist here as real content, not pointer stubs,
# as long as the platform's checkout step already resolved LFS pointers before handing
# the context to Docker. If it ever hands over raw pointer files instead, pulling them
# here would need repo/.git context that a build context alone does not include.
COPY . .

# The full local dataset (data/jobs.db, data/jobs.faiss) is too large for this
# platform's free-tier RAM limit. data/deploy/ holds a smaller stratified sample
# built by scripts/build_deploy_dataset.py + scripts/generate_embeddings.py,
# swapped in here so local dev keeps the full dataset untouched.
RUN cp data/deploy/jobs.db data/jobs.db && cp data/deploy/jobs.faiss data/jobs.faiss

ENV OMP_NUM_THREADS=1
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
