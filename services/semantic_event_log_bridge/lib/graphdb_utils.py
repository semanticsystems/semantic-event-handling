import logging
from rdflib import Graph
import requests
from configuration import GraphDbConfiguration

def insert_graph(config: GraphDbConfiguration, graph: Graph):
    logging.debug(f"Inserting graph into GraphDB...")
    graph.serialize(destination="graph.ttl", format="turtle")
    with open("graph.ttl", "rb") as graph_file:
        requests.post(
            f"http://{config.host}:{config.port}/repositories/{config.repository}/statements",
            data=graph_file,
            headers={"Content-Type": "text/turtle"},
        )