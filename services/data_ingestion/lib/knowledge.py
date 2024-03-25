from dataclasses import dataclass
import re
from lib.data_source import (
    DataSource,
    InfluxDBConfiguration,
    InfluxDataSource,
    PointDescription,
)

from configuration import GraphDbConfiguration
from lib.exceptions import KnowledgeBaseException
from lib.graphdb_utils import get_string, get_uri, query_multiple

class KnowledgeRepository:
    def __init__(self, graphDbConfig: GraphDbConfiguration) -> None:
        self.graphDbConfig = graphDbConfig

    def find_all_points(self) -> [DataSource]:
        # Find InfluxDB points
        bindings = query_multiple(
            self.graphDbConfig,
            """
            PREFIX brick: <https://brickschema.org/schema/Brick#>
            PREFIX ref: <https://brickschema.org/schema/Brick/ref#>
            PREFIX sosa: <http://www.w3.org/ns/sosa/>

            select ?point ?timeseries_id ?db_address ?db_port ?db_protocol ?db_token ?db_org ?db_bucket where { 
                ?point rdf:type sosa:Sensor .
                ?point ref:hasTimeseriesId ?timeseries_id .
                ?point ref:storedAt ?db .
                ?db rdf:type ref:InfluxDatabase .
                ?db ref:address ?db_address .
                ?db ref:port ?db_port .
                ?db ref:protocol ?db_protocol .
                ?db ref:token ?db_token .
                ?db ref:org ?db_org .
                ?db ref:bucket ?db_bucket .
            }
            """
        )

        results = []
        for binding in bindings:
            uri = get_uri("point", binding)
            timeseries_id = get_string("timeseries_id", binding)
            db_address = get_string("db_address", binding)
            db_port = get_string("db_port", binding)
            db_protocol = get_string("db_protocol", binding)
            db_token = get_string("db_token", binding)
            db_org = get_string("db_org", binding)
            db_bucket = get_string("db_bucket", binding)
            config = InfluxDBConfiguration(
                db_address, db_port, db_protocol, db_token, db_org, db_bucket
            )
            data_source = create_influxdb_data_source(config, uri, timeseries_id)
            results.append(data_source)
        return results

TIMESERIES_ID_REGEX = r"measurement=(\w+),field=(\w+)"


def create_influxdb_data_source(
    config: InfluxDBConfiguration, uri: str, timeseries_id: str
) -> PointDescription:
    match = re.match(TIMESERIES_ID_REGEX, timeseries_id)
    if not match:
        raise KnowledgeBaseException(
            f"Timeseries ID {timeseries_id} does not match expected format."
        )
    measurement = match.group(1)
    field = match.group(2)
    point_wrapper = PointDescription(uri, measurement, field)
    return InfluxDataSource(config, point_wrapper)
