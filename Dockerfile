FROM python:3.7.4-alpine3.10

LABEL org.opencontainers.image.source https://github.com/MarshallWace/push-gateway-pruner

RUN apk add --no-cache git libffi-dev gcc musl-dev

# Copy ca cert files for SSL. dummyfile as a hack for copy if file exists
ARG CA_CERT_PATH
COPY dummyfile .$CA_CERT_PATH* /
ENV REQUESTS_CA_BUNDLE=${CA_CERT_PATH:+$CA_CERT_PATH}

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.1.13

# System deps:
RUN pip install -U pip
RUN pip install "poetry==$POETRY_VERSION"

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi

# Creating folders, and files for a project:
COPY . /code


ENTRYPOINT ["python3","push_gateway_pruner.py"]