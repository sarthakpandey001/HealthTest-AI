# Use an official Python runtime as a parent image
# python:3.11-slim-buster is a good choice for smaller image size
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    # Cloud Run default port is 8080. It is set as an env var.
    PORT=8080

## 🐳 Stage 1: Install System Dependencies (Combined & Cleaned Up)
RUN apt-get update && \
    apt-get install -y libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgdk-pixbuf-xlib-2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libnss3 lsb-release xdg-utils wget libcurl3t64-gnutls libldap2 libnghttp3-9 libngtcp2-crypto-gnutls8 libsasl2-2 libsasl2-modules-db libldap-common libnghttp2-14 libngtcp2-16 librtmp1 libsasl2-modules libssh2-1t64 git && \
    # Cleanup for smaller image size
    rm -rf /var/lib/apt/lists/*

# Download and install Google Chrome using a single, robust RUN command.
RUN CHROME_SETUP=google-chrome.deb && \
    wget -O $CHROME_SETUP "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" && \
    dpkg -i $CHROME_SETUP || apt-get install -y -f && \
    rm $CHROME_SETUP

# Copy requirements.txt and install them to leverage Docker's build cache.
COPY refactored/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY refactored .

# Cloud Run expects the application to listen on $PORT.
# Use Gunicorn to run the application. The format `app:app` is correct for a
# module `app.py` containing an application instance `app`.
# Common starting point for 1 vCPU: workers=1, threads=8.
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 app:app

