import json


class MqttConfiguration:
    def __init__(self, config: dict) -> None:
        self.host = config["host"]
        self.port = config["port"]
        self.client_id = config["clientId"]


class GraphDbConfiguration:
    def __init__(self, config: dict) -> None:
        self.host = config["host"]
        self.port = config["port"]
        self.repository = config["repository"]


class Configuration:
    def __init__(self, config: dict) -> None:
        self.mqtt = MqttConfiguration(config["mqtt"])
        self.event_log = GraphDbConfiguration(config["event_log"])


def load_configuration(path: str) -> Configuration:
    with open(path) as config_file:
        json_data = json.loads(config_file.read())
        return Configuration(json_data)
