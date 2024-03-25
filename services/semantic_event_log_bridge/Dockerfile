FROM python:3.12-alpine

COPY . /opt/semantic_event_log_bridge

RUN pip3 install -r /opt/semantic_event_log_bridge/requirements.txt

WORKDIR /opt/semantic_event_log_bridge

ENTRYPOINT [ "python3", "semantic_event_log_bridge.py", "-c", "config/config.docker.json" ]