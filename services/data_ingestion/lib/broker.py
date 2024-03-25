from pyparsing import abstractmethod
from rdflib import Graph, Literal, Namespace, URIRef
from configuration import MqttConfiguration
from lib.model import Event
import paho.mqtt.client as mqtt

RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
SOSA = Namespace("http://www.w3.org/ns/sosa/")
SENSE = Namespace("http://w3id.org/explainability/")
EX = Namespace("http://auto.tuwien.ac.at/example#")

class EventBroker:
    @abstractmethod
    def publish(self, event: Event) -> None:
        pass


class MqttEventBroker(EventBroker):
    def __init__(self, configuration: MqttConfiguration) -> None:
        self.configuration = configuration
        self.client = mqtt.Client(client_id=configuration.client_id)
        self.client.connect(configuration.host, configuration.port)

    def publish(self, event: Event) -> None:
        """
        Publishes a new event on the event broker.
        """
        simple_name = event.source.split("#")[-1]
        epoch_in_s = int(event.timestamp.timestamp())

        # This naming scheme only allows a single event per second. A real implementation would use a more fine-grained
        # naming scheme.
        observation_uri = SENSE[f"event_{simple_name}_{epoch_in_s}"]
        graph = Graph()
        graph.bind("sense", SENSE)
        graph.add((observation_uri, RDF["type"], SOSA["Observation"]))
        graph.add((URIRef(event.source), SOSA["madeObservation"], observation_uri))
        graph.add((observation_uri, SOSA["resultTime"], Literal(event.timestamp)))
        graph.add((observation_uri, SOSA["hasSimpleResult"], Literal(event.value)))

        payload = graph.serialize(format="turtle")
        self.client.publish("events/sensors", payload)
