FROM python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e AS base
ARG APP_REVISION=development
ARG REVISION
ARG APP_SOURCE_URL=https://github.com/xsolutionsmd/oasis-kebab-house
LABEL org.opencontainers.image.source=$APP_SOURCE_URL
LABEL org.opencontainers.image.revision=${APP_REVISION}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data
WORKDIR /workspace
COPY app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && useradd -u 10001 -m oasis && mkdir /data && chown oasis:oasis /data
COPY --chown=oasis:oasis app/ /workspace/
RUN printf '%s' "${REVISION:-$APP_REVISION}" > /workspace/revision.txt
USER oasis
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=4s --start-period=15s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3)"
FROM base AS development
CMD ["gunicorn","--bind","0.0.0.0:8080","--workers","1","--threads","4","--timeout","45","--config","gunicorn.conf.py","wsgi:app"]
FROM base AS check
CMD ["python","-m","pytest","-q","tests"]
FROM base AS test
RUN python -m pytest -q -p no:cacheprovider tests
FROM base AS runtime
CMD ["gunicorn","--bind","0.0.0.0:8080","--workers","1","--threads","4","--timeout","45","--config","gunicorn.conf.py","wsgi:app"]
FROM runtime AS production
