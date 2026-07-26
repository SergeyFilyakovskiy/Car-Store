FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"


RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/*


ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal


COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY ./entrypoint.sh /app/entrypoint.sh
RUN sed -i 's/\r$//g' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

COPY . .

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
