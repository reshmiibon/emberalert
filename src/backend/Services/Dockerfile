FROM python:3.11.8-bookworm


RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install \
    flask \
    flask-cors \
    mysql-connector-python \
    requests 