import argparse
import datetime
import logging
import paho.mqtt.client as mqtt
from rdflib import Graph, Literal, Namespace
from configuration import MqttConfiguration, load_configuration

RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
SOSA = Namespace("http://www.w3.org/ns/sosa/")
SENSE = Namespace("http://w3id.org/explainability/")
EX = Namespace("http://auto.tuwien.ac.at/example#")


def connect_to_mqtt_broker(config: MqttConfiguration) -> mqtt.Client:
    client = mqtt.Client(config.client_id)
    client.connect(config.host, config.port)
    return client

class EstimatorModel:
    def __init__(self, coef1: float, coef2: float, intercept: float) -> None:
        self.coef1 = coef1
        self.coef2 = coef2
        self.intercept = intercept
    
    def predict(self, setpoint_temp: float, outside_temp: float) -> float:
        return self.coef1 * setpoint_temp + self.coef2 * outside_temp + self.intercept

class EventDetectionContext:
    def __init__(self, mqtt_client: mqtt.Client, model: EstimatorModel) -> None:
        self.mqtt_client = mqtt_client
        self.knowledge_graph = Graph()
        self.active_events_types = set()
        self.model = model

    def handle_event(self, client, userdata, msg) -> None:
        new_dynamic_graph = Graph().parse(data=msg.payload, format="turtle")

        # remove old observations of this sensor
        # This assumes that there is only one observation per sensor per message
        obs_triples = new_dynamic_graph.triples((None, SOSA["madeObservation"], None))
        for obs_triple in obs_triples:
            for old_observation in self.knowledge_graph.triples(
                (obs_triple[0], SOSA["madeObservation"], None)
            ):
                self.knowledge_graph.remove(
                    (old_observation[2], SOSA["hasSimpleResult"], None)
                )
                self.knowledge_graph.remove(
                    (old_observation[2], SOSA["resultTime"], None)
                )
                self.knowledge_graph.remove(old_observation)

        self.knowledge_graph += new_dynamic_graph
        self.detect_events()

    def detect_events(self) -> None:
        def get_single_observation(sensor: str) -> str:
            triples = list(self.knowledge_graph.triples((EX[sensor], SOSA["madeObservation"], None)))

            # if we do not have any observations, we can stop here
            if len(list(triples)) == 0:
                return None

            # assert that there is only one observation per sensor
            if len(list(triples)) > 1:
                raise ValueError("There should be only one observation per sensor")

            # get the result of the observation
            observation = list(triples)[0][2]
            result = list(self.knowledge_graph.triples((observation, SOSA["hasSimpleResult"], None)))
            if len(list(result)) != 1:
                raise ValueError("There should be only one result per observation")
            
            return list(result)[0][2].toPython()

        # get the result of the observation
        setpoint_temp = get_single_observation("T_set")
        outside_temp = get_single_observation("T_out")
        current_power = get_single_observation("P_el")

        # if we do not have all observations, we can stop here
        if setpoint_temp is None or outside_temp is None or current_power is None:
            return
        
        # obtain the maximum power from the model
        max_power = self.model.predict(setpoint_temp, outside_temp)

        # get only the inferred parts of the graph that are related to an event
        inferred_event_graph = Graph()
        inferred_event_graph.bind("s", SENSE)
        inferred_event_graph.bind("ex", EX)

        timestamp = datetime.datetime.now(tz=datetime.UTC)
        timestamp_in_ms = int(timestamp.timestamp() * 1000)

        pc_high_event_name = "PowerConsumptionHighEvent_" + str(timestamp_in_ms)
        pc_high_type = EX["PowerConsumptionHighEvent"]
        pc_high_obs = EX["obs_" + pc_high_event_name]
        pc_high = EX["event_" + pc_high_event_name]
        if current_power > max_power and not pc_high_type in self.active_events_types:
            inferred_event_graph.add((EX["P_el"], SOSA["madeObservation"], pc_high_obs))
            inferred_event_graph.add((pc_high_obs, RDF["type"], SOSA["Observation"]))
            inferred_event_graph.add((pc_high_obs, SOSA["resultTime"], Literal(timestamp)))
            inferred_event_graph.add((pc_high_obs, SOSA["usedProcedure"], SENSE["HeatingPowerConsumptionModel"]))
            inferred_event_graph.add((pc_high_obs, SOSA["hasResult"], pc_high))
            inferred_event_graph.add((pc_high, RDF["type"], pc_high_type))
            self.active_events_types.add(pc_high_type)
        elif current_power <= max_power and pc_high_type in self.active_events_types:
            self.active_events_types.remove(pc_high_type)

        pc_normal_event_name = "PowerConsumptionIsNormalEvent_" + str(timestamp_in_ms)
        pc_normal_type = SENSE["PowerConsumptionIsNormalEvent"]
        pc_normal_obs = SENSE["obs_" + pc_normal_event_name]
        pc_normal = SENSE["event_" + pc_normal_event_name]
        if current_power <= max_power and not pc_normal_type in self.active_events_types:
            inferred_event_graph.add((EX["P_el"], SOSA["madeObservation"], pc_normal_obs))
            inferred_event_graph.add((pc_normal_obs, RDF["type"], SOSA["Observation"]))
            inferred_event_graph.add((pc_normal_obs, SOSA["resultTime"], Literal(timestamp)))
            inferred_event_graph.add((pc_normal_obs, SOSA["usedProcedure"], SENSE["HeatingPowerConsumptionModel"]))
            inferred_event_graph.add((pc_normal_obs, SOSA["hasResult"], pc_normal))
            inferred_event_graph.add((pc_normal, RDF["type"], pc_normal_type))
            self.active_events_types.add(pc_normal_type)
        elif current_power > max_power and pc_normal_type in self.active_events_types:
            self.active_events_types.remove(pc_normal_type)

        if len(inferred_event_graph) > 0:
            payload = inferred_event_graph.serialize(format="turtle")
            self.mqtt_client.publish("events/simple", payload)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(prog="rule_based_event_detection.py")
    arg_parser.add_argument("-c", "--config", required=True)
    args = arg_parser.parse_args()
    config = load_configuration(args.config)

    # The model parameters are obtained from the learn_model.py script.
    # We did NOT use realistic data for this example! We simply want to
    # demonstrate how a model might be integrated in the event detection
    # architecture.
    model = EstimatorModel(1.35442514, -2.44830438, 26.776261373035624)

    logging.basicConfig(level=logging.INFO)
    logging.info("Model-based Event Detection Service starting...")

    # connect to the MQTT broker
    mqtt_client = connect_to_mqtt_broker(config.mqtt)

    # create the event detection context
    event_detection_context = EventDetectionContext(mqtt_client, model)
    mqtt_client.on_message = event_detection_context.handle_event

    # subscribe to the events/sensors topic
    mqtt_client.subscribe("events/sensors")
    mqtt_client.loop_forever()

    logging.info("Monitoring Service shutting down...")
