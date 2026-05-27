FROM jenkins/jenkins:lts-jdk17

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Databricks CLI and Python tools
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir \
    databricks-cli \
    databricks-sdk \
    flake8 \
    black \
    bandit \
    pytest \
    pytest-cov \
    requests

ENV PATH="/opt/venv/bin:${PATH}"

# Install Jenkins plugins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Copy pipeline configuration
COPY casc.yaml /usr/share/jenkins/ref/casc.yaml
ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc.yaml

USER jenkins
