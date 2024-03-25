FROM python:3.12-alpine

COPY . /opt/data_ingestion

RUN pip3 install -r /opt/data_ingestion/requirements.txt

WORKDIR /opt/data_ingestion

ENTRYPOINT [ "python3", "data_ingestion.py", "-c", "config/config.docker.json" ]