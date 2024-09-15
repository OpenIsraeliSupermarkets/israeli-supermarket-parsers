FROM python:3.8.3-slim

WORKDIR /usr/src/app

COPY . .
RUN pip install -r requirements.txt
RUN apt-get update && apt-get -y install git
RUN pip install black
RUN pip install pylint

RUN git config --global --unset user.name && git config --global --unset user.email && git config --global --unset user.signingkey
ENTRYPOINT ["python3", "main.py"]