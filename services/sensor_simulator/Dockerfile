FROM python:3.12-alpine

COPY . /opt/sensor_simulator

RUN pip3 install -r /opt/sensor_simulator/requirements.txt

WORKDIR /opt/sensor_simulator

ENTRYPOINT [ "python3", "sensor_simulator.py", "-c", "config/config.docker.json" ]