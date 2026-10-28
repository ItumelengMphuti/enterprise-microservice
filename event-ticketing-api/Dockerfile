# Stage 1: Install Python dependencies
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Run the Django application
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/django

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

RUN python -m pip uninstall -y pip

RUN addgroup --system django \
    && adduser --system --home /home/django --ingroup django django \
    && mkdir -p /home/django \
    && chown -R django:django /app /home/django

USER django

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
