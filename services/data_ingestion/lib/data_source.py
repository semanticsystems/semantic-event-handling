from abc import abstractmethod
from dataclasses import dataclass
import datetime
from typing import Iterator, List
from influxdb_client import InfluxDBClient

class DataSource:
    @classmethod
    @abstractmethod
    def uri(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def get_points(self, from_time_ns: int, to_time_ns: int) -> List[tuple[int, float]]:
        pass


@dataclass
class PointDescription:
    uri: str
    measurement: str
    field: str


class InfluxDBConfiguration:
    def __init__(self, host: str, port: str, protocol: str, token: str, org: str, bucket: str) -> None:
        self.host = host
        self.port = port
        self.protocol = protocol
        self.token = token
        self.org = org
        self.bucket = bucket


class InfluxDataSource(DataSource):
    def __init__(self, config: InfluxDBConfiguration, point: PointDescription) -> None:
        # Only http protocol is supported
        if config.protocol != "http":
            raise Exception("Only http protocol is supported")

        self.config = config
        self.client = InfluxDBClient(
            url=f"{config.protocol}://{config.host}:{config.port}",
            token=config.token,
            org=config.org,
        )
        self.point = point

    def uri(self) -> str:
        return self.point.uri

    def get_points(self, from_time: datetime.datetime, to_time: datetime.datetime) -> Iterator[tuple[int, float]]:
        query = f"""
        from(bucket: "{self.config.bucket}")
            |> range(start: {from_time.isoformat()}, stop: {to_time.isoformat()})
            |> filter(fn:(r) => r._measurement == "{self.point.measurement}")
            |> filter(fn:(r) => r._field == "{self.point.field}")
        """
        result_stream = self.client.query_api().query_stream(
            org=self.client.org, query=query
        )
        for result in result_stream:
            yield (result.get_time(), result.get_value())
