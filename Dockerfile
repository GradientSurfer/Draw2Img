FROM python:3.11-slim-bookworm

WORKDIR /app
COPY LICENSE LICENSE
COPY README.md README.md
COPY pyproject.toml pyproject.toml
COPY ./draw2img ./draw2img
RUN --mount=type=cache,target=/root/.cache/pip pip install .
ENV HF_HOME=/root/.cache/huggingface
CMD ["python3", "draw2img/main.py", "--host", "0.0.0.0"]