FROM python:3.11-slim

WORKDIR /app

# Install pinned deps first (cached layer; only invalidates when lockfile changes)
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

# Then install the local package itself (skip its deps — they're already in)
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir --no-deps -e .

ENV DATA_DIR=/data
VOLUME ["/data"]

EXPOSE 8000

CMD ["python", "-m", "src"]
