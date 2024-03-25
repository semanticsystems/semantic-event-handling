import argparse
import datetime
import logging
import time
from lib.model import Event
from lib.broker import MqttEventBroker
from lib.knowledge import KnowledgeRepository
from configuration import GraphDbConfiguration, load_configuration
from lib.data_source import DataSource
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(wait=wait_fixed(2), stop=stop_after_attempt(10))
def find_all_points(config: GraphDbConfiguration) -> [DataSource]:
    knowledge_repository = KnowledgeRepository(config)
    return knowledge_repository.find_all_points()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Data Ingestion starting...")

    arg_parser = argparse.ArgumentParser(prog="data_ingestion.py")
    arg_parser.add_argument("-c", "--config", required=True)
    args = arg_parser.parse_args()

    config = load_configuration(args.config)

    logging.info("Running Data Ingestion...")
    data_sources = find_all_points(config.semantic_model)
    logging.info(f"Importing values from {len(data_sources)} data sources...")

    event_broker = MqttEventBroker(config.mqtt)
    last_import = datetime.datetime.now(tz=datetime.UTC)

    logging.info(f"Starting importing ...")
    while True:
        now = datetime.datetime.now(tz=datetime.UTC)
        logging.debug(f"Importing in range {last_import} - {now}")
        for data_source in data_sources:
            point_values = list(data_source.get_points(last_import, now))
            logging.debug(f"Found {len(point_values)} values for {data_source.uri()}")
            for timestamp, value in point_values:
                event_broker.publish(Event(data_source.uri(), timestamp, value))
        last_import = now
        time.sleep(5)
