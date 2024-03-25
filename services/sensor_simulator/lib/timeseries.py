import time
from influxdb_client import InfluxDBClient, Point
from configuration import InfluxDbConfiguration
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxDBRepository:
    def __init__(self, config: InfluxDbConfiguration) -> None:
        self.config = config
        self.client = InfluxDBClient(
            url=f"http://{config.host}:{config.port}",
            token=config.token,
            org=config.org
        )

    def wait_for_ready(self) -> None:
        tries = 0
        while tries < 10:
            try:
                response = self.client.ready()
                if response.status == "ready":
                    break
            except:
                time.sleep(1)
            finally:
                tries += 1

    def write_point(self, point: Point) -> None:
        self.client.write_api(write_options=SYNCHRONOUS).write(bucket=self.config.bucket, record=point)
