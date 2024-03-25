import argparse
import logging
import paho.mqtt.client as mqtt
from pyshacl import validate
from rdflib import Graph, Namespace
from configuration import MqttConfiguration, load_configuration

RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
SOSA = Namespace("http://www.w3.org/ns/sosa/")
SENSE = Namespace("http://w3id.org/explainability/")
EX = Namespace("http://auto.tuwien.ac.at/example#")

def connect_to_mqtt_broker(config: MqttConfiguration) -> mqtt.Client:
    client = mqtt.Client(config.client_id)
    client.connect(config.host, config.port)
    return client


class EventDetectionContext:
    def __init__(
        self, mqtt_client: mqtt.Client, static_graph: Graph, shapes_graph: Graph
    ) -> None:
        self.mqtt_client = mqtt_client
        self.knowledge_graph = static_graph
        self.shapes_graph = shapes_graph
        self.active_events = set()

    def handle_event(self, client, userdata, msg) -> None:
        new_dynamic_graph = Graph().parse(data=msg.payload, format="turtle")

        # remove old observations of this sensor
        # This assumes that there is only one observation per sensor per message
        obs_triples = new_dynamic_graph.triples((None, SOSA["madeObservation"], None))
        for obs_triple in obs_triples:
            for old_observation in self.knowledge_graph.triples((obs_triple[0], SOSA["madeObservation"], None)):
                self.knowledge_graph.remove((old_observation[2], SOSA["hasSimpleResult"], None))
                self.knowledge_graph.remove((old_observation[2], SOSA["resultTime"], None))
                self.knowledge_graph.remove(old_observation)

        self.knowledge_graph += new_dynamic_graph
        self.detect_events()

    def detect_events(self) -> None:
        # This has horrendous performance. It is just a proof of concept. Otherwise the detected events would
        # accumulate in the graph.
        graph_copy = Graph().parse(data=self.knowledge_graph.serialize(format="turtle"), format="turtle")
        validate(
            graph_copy,
            shacl_graph=self.shapes_graph,
            inference="none",
            abort_on_first=False,
            allow_infos=False,
            allow_warnings=False,
            meta_shacl=False,
            advanced=True,  # needed to execute shacl rules
            js=False,
            debug=False,
            inplace=True
        )

        # get only the inferred parts of the graph that are related to an event
        inferred_graph = Graph()
        inferred_graph.bind("s", str(SENSE))
        inferred_graph.bind("ex", str(EX))
        
        detected_events = set()
        for event in graph_copy.triples((None, RDF["type"], SENSE["Event"])):
            event_uri = event[0]
            other_types = list(filter(lambda t: t[2] != SENSE["Event"], graph_copy.triples((event_uri, RDF["type"], None))))
            if len(other_types) == 1:
                detected_events.add((event_uri, other_types[0][2]))
            else:
                logging.warning(f"Found event with multiple types other than Event: {event_uri}")
        
        for event, event_type in detected_events:
            if event_type not in self.active_events:
                inferred_graph += graph_copy.triples((event, None, None))
                observation = list(graph_copy.triples((None, SOSA["hasResult"], event)))[0][0]
                inferred_graph += graph_copy.triples((observation, None, None))

        if len(inferred_graph) > 0:
            payload = inferred_graph.serialize(format="turtle")
            self.mqtt_client.publish("events/simple", payload)
        
        self.active_events = {event_type for _, event_type in detected_events}

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog="rule_based_event_detection.py")
    arg_parser.add_argument("-c", "--config", required=True)
    args = arg_parser.parse_args()
    config = load_configuration(args.config)

    logging.basicConfig(level=logging.INFO)
    logging.info("Rule-based Event Detection Service starting...")

    # connect to the MQTT broker
    mqtt_client = connect_to_mqtt_broker(config.mqtt)

    # load the shacl shapes
    shapes_graph = Graph().parse("data/shacl_rules.ttl", format="turtle")

    # create the event detection context
    event_detection_context = EventDetectionContext(
        mqtt_client, Graph(), shapes_graph
    )
    mqtt_client.on_message = event_detection_context.handle_event

    # subscribe to the events/sensors topic
    mqtt_client.subscribe("events/sensors")
    mqtt_client.loop_forever()

    logging.info("Monitoring Service shutting down...")
