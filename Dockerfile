# SiteForge is a Python (Flask) app that also shells out to npm / next to
# build and preview each generated site, so the image needs both runtimes.
# Node 20 is copied in from the official Node image; both images are Debian
# bookworm, so the node binary is compatible.
FROM node:20-bookworm-slim AS node

FROM python:3.12-slim-bookworm

COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
 && node --version && npm --version

# A bold TTF for the share image (og.png) text; resvg and Pillow find it.
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# One worker: preview servers, deploy status and search jobs live in this
# process's memory. Threads give concurrency; the long timeout covers a
# site build's npm install, which runs inside the request.
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 16 --timeout 600
