import argparse
import logging
import paho.mqtt.client as mqtt
from rdflib import Graph, Namespace
from configuration import MqttConfiguration, load_configuration
from lib.graphdb_utils import insert_graph
from tenacity import retry, stop_after_attempt, wait_fixed

RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
SOSA = Namespace("http://www.w3.org/ns/sosa/")
SENSE = Namespace("http://w3id.org/explainability/")
EX = Namespace("http://auto.tuwien.ac.at/example#")


@retry(wait=wait_fixed(2), stop=stop_after_attempt(10))
def connect_to_mqtt_broker(config: MqttConfiguration) -> mqtt.Client:
    client = mqtt.Client(config.client_id)
    client.connect(config.host, config.port)
    return client


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog="rule_based_event_detection.py")
    arg_parser.add_argument("-c", "--config", required=True)
    args = arg_parser.parse_args()
    config = load_configuration(args.config)

    logging.basicConfig(level=logging.INFO)
    logging.info("Semantic Event Log Bridge starting...")

    # connect to the MQTT broker
    mqtt_client = connect_to_mqtt_broker(config.mqtt)

    # set message callback
    def send_data_to_event_log(client, userdata, msg):
        logging.debug("Sending data to event log...")
        new_dynamic_graph = Graph().parse(data=msg.payload, format="turtle")
        insert_graph(config.event_log, new_dynamic_graph)

    mqtt_client.on_message = send_data_to_event_log

    # subscribe to the events/sensors topic
    mqtt_client.subscribe("events/simple")
    mqtt_client.subscribe("events/complex")
    mqtt_client.loop_forever()

    logging.info("Monitoring Service shutting down...")
