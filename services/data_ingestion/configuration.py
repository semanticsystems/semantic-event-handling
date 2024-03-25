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


class InfluxDbConfiguration:
    """Configuration for InfluxDB"""
    def __init__(self, config: dict) -> None:
        self.host = config["host"]
        self.port = config["port"]
        self.org = config["org"]
        self.token = config["token"]
        self.bucket = config["bucket"]


class Configuration:
    def __init__(self, config: dict) -> None:
        self.mqtt = MqttConfiguration(config["mqtt"])
        self.semantic_model = GraphDbConfiguration(config["semantic_model"])


def load_configuration(path: str) -> Configuration:
    with open(path) as config_file:
        json_data = json.loads(config_file.read())
        return Configuration(json_data)
