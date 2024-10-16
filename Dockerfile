#syntax=docker/dockerfile:1

FROM node:20-bookworm as base
WORKDIR /usr/src/app
ARG PY_VERSION="3.11.0"
ENV TZ="Asia/Jerusalem"

RUN apt-get update && \
    apt-get install python3-pip -y && \
    apt-get install dieharder -y && \
    apt-get install wget -y && \
    apt-get clean && \
    apt-get autoremove

ENV HOME="/root"
WORKDIR ${HOME}
RUN apt-get install -y git libbz2-dev libncurses-dev  libreadline-dev libffi-dev libssl-dev build-essential python3-dev
RUN git clone --depth=1 https://github.com/pyenv/pyenv.git .pyenv
ENV PYENV_ROOT="${HOME}/.pyenv"
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"

RUN pyenv install $PY_VERSION
RUN pyenv global $PY_VERSION

COPY . .

RUN pip install -r requirements.txt

FROM base as prod
CMD python main.py

FROM base as dev

RUN pip install -r requirements-dev.txt

FROM base as test
VOLUME ["/usr/src/app/temp"]

RUN python -m pip install . ".[test]"
CMD python -m pytest .
