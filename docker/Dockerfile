FROM python:3.8.12-buster

ARG SANDBOX_USER_UID
ARG SANDBOX_DIR

COPY ./src/PABCNETC.zip /usr/bin/pascal
RUN apt-get update && \
    apt-get -y install nano mono-complete && \
    pip install --upgrade pip && \
    pip install pipenv && \
    unzip /usr/bin/pascal/PABCNETC -d /usr/bin/pascal

RUN adduser \
    --system \
    --gecos \
    --disabled-login \
    --disabled-password \
    --home ${SANDBOX_DIR} \
    --uid ${SANDBOX_USER_UID} \
    sandbox && \
    chown root:root ${SANDBOX_DIR}

COPY ./src/Pipfile ./src/Pipfile.lock /tmp/
RUN cd /tmp && pipenv install --deploy --dev --system

WORKDIR ${SANDBOX_DIR}