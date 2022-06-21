FROM python:3.8.12-buster

ARG SANDBOX_USER_UID
ARG SANDBOX_DIR

RUN apt-get update && \
    apt-get -y install nano mono-complete && \
    pip install --upgrade pip && \
    pip install pipenv
COPY ./src/PABCNETC.zip /usr/bin/pascal/PABCNETC.zip
RUN unzip /usr/bin/pascal/PABCNETC -d /usr/bin/pascal

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