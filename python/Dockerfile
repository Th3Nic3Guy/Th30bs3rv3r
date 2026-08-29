# Simulation engine image, run on the per-run Compute Engine instance (PRD Section 6.0).
# One instance runs exactly one simulation run for its full lifetime.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY freewill/ freewill/
COPY pyproject.toml .
RUN pip install --no-cache-dir --no-deps -e .

# Entry point is left to the deployment: the Go orchestrator (go/cmd/orchestrator, PRD
# Section 9) invokes this image with a run_id it has already registered in Cloud SQL
# (freewill.storage.run_registry) and cached in Redis (freewill.storage.config_cache).
ENTRYPOINT ["python", "-m", "freewill"]
