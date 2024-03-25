import json


class InfluxDbConfiguration:
    def __init__(self, config: dict) -> None:
        self.host = config["host"]
        self.port = config["port"]
        self.org = config["org"]
        self.token = config["token"]
        self.bucket = config["bucket"]


class Configuration:
    def __init__(self, config: dict) -> None:
        self.influxdb = InfluxDbConfiguration(config["influxdb"])


def load_configuration(path: str) -> Configuration:
    with open(path) as config_file:
        json_data = json.loads(config_file.read())
        return Configuration(json_data)
