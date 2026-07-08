# Small, reproducible runtime for the harness. No dependencies beyond Python.
FROM python:3.12-slim

WORKDIR /app
COPY harness/ harness/
COPY demos/ demos/
COPY data/ data/
COPY tests/ tests/

# Default: prove the container is healthy by running the offline test suite.
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]

# Interactive demo:
#   docker build -t agent-harness .
#   docker run -it agent-harness python demos/inbox_copilot.py
# Live mode (pass your own key at runtime - never bake keys into images):
#   docker run -it -e GEMINI_API_KEY=your-key agent-harness python demos/inbox_copilot.py
