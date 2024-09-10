FROM python:3.8.3-slim

WORKDIR /usr/src/app

COPY . .
RUN pip install -r requirements.txt



ENTRYPOINT ["python3", "main.py"]