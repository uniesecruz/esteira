# Fortify SCA Docker Container
# NOTE: Fortify Static Code Analyzer requires a commercial license from OpenText.
# This Dockerfile provides the structure for integration. You must:
# 1. Obtain a Fortify SCA license
# 2. Download the Fortify SCA installer
# 3. Place the installer and license in this directory before building
#
# For evaluation, Bandit (included in the pipeline) provides similar
# static security analysis for Python code.

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir bandit flake8

# Fortify SCA installation placeholder
# Uncomment and adjust when you have the Fortify installer:
# COPY Fortify_SCA_*.run /tmp/fortify-installer.run
# RUN chmod +x /tmp/fortify-installer.run && \
#     /tmp/fortify-installer.run --mode unattended && \
#     rm /tmp/fortify-installer.run

# License placeholder
RUN mkdir -p /opt/fortify/license /opt/fortify/data
# COPY fortify.license /opt/fortify/license/fortify.license

COPY fortify-scan.sh /usr/local/bin/fortify-scan.sh
RUN chmod +x /usr/local/bin/fortify-scan.sh

WORKDIR /usr/src/app

ENTRYPOINT ["/usr/local/bin/fortify-scan.sh"]
