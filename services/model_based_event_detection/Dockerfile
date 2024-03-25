FROM python:3.12-alpine

COPY . /opt/model_based_event_detection

RUN pip3 install -r /opt/model_based_event_detection/requirements.txt

WORKDIR /opt/model_based_event_detection

ENTRYPOINT [ "python3", "model_based_event_detection.py", "-c", "config/config.docker.json" ]