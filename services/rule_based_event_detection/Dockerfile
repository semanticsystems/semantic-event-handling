FROM python:3.12-alpine

COPY . /opt/rule_based_event_detection

RUN pip3 install -r /opt/rule_based_event_detection/requirements.txt

WORKDIR /opt/rule_based_event_detection

ENTRYPOINT [ "python3", "rule_based_event_detection.py", "-c", "config/config.docker.json" ]