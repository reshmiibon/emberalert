FROM python:3.11.8-bookworm

RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install \
    earthengine-api \
    flask \
    flask-cors \
    hdbscan \
    matplotlib \
    mysql-connector-python \
    pandas \
    pillow \
    requests \
    schedule \
    scikit-learn \
    scipy \
    tensorflow \
    xmltodict

# gcloud setup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    gnupg \
    curl
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    apt-get update -y && \
    apt-get install google-cloud-sdk -y

# Install Google Cloud SDK
RUN curl -sSL https://sdk.cloud.google.com | bash
