# ==============================================================================
# BHU LOKA (भूलोक) - Google Cloud Run Container Specification
# Multi-stage lightweight Debian Python container
# Author: Prince Kumar (IIT Patna) & Payal Priyadarshini (IIITDM Jabalpur)
# Supervisor: Dr. Pallav Rustogi
# ==============================================================================

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    BHU_LOKA_INDIA_DB_PATH=/app/Data/01_Boundaries/bhu_loka_india_intel.sqlite \
    PYTHONPATH=/app:/app/Pipelines:/app/Models/04_Hybrid_RAG/enterprise_rag_app

# Install minimal system dependencies for SQLite R-Tree and C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python production dependencies
COPY requirements-docker.txt /app/
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy backend application code, pipelines, and models
COPY Pipelines/ /app/Pipelines/
COPY Models/04_Hybrid_RAG/ /app/Models/04_Hybrid_RAG/
COPY Models/Checkpoints/ /app/Models/Checkpoints/

# Copy SQLite Spatial Reference Database & Processed Numerical Arrays
COPY Data/01_Boundaries/bhu_loka_india_intel.sqlite /app/Data/01_Boundaries/
COPY Data/08_Processed_Outputs/ /app/Data/08_Processed_Outputs/

# Copy Frontend Workstation & Assets for Unified Static Serving
COPY bhu_loka_cyber_dashboard.html /app/
COPY index.html /app/
COPY bhu_loka_leafmap_interactive.html /app/
COPY BHU_LOKA_Presentation_Amour_Hoffen.html /app/
COPY Assets/ /app/Assets/

# Non-root security user
RUN useradd -m -u 1000 bhuloka && chown -R bhuloka:bhuloka /app
USER bhuloka

EXPOSE 8080

CMD ["sh", "-c", "uvicorn Models.04_Hybrid_RAG.enterprise_rag_app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
