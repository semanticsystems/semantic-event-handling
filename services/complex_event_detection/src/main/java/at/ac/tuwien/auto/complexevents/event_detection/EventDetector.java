package at.ac.tuwien.auto.complexevents.event_detection;

import java.io.IOException;
import java.io.InputStream;
import java.io.StringWriter;

import org.apache.log4j.Logger;
import org.eclipse.paho.client.mqttv3.MqttClient;

import com.hp.hpl.jena.rdf.model.Model;
import com.hp.hpl.jena.rdf.model.ModelFactory;
import com.hp.hpl.jena.util.FileManager;

import at.ac.tuwien.auto.complexevents.configuration.EventDetectorConfig;
import eu.larkc.csparql.core.engine.CsparqlEngineImpl;
import eu.larkc.csparql.core.engine.CsparqlQueryResultProxy;

public class EventDetector {
    private static final Logger logger = Logger.getLogger(EventDetector.class);

    private final EventDetectorConfig config;

    public EventDetector(EventDetectorConfig config) {
        this.config = config;
    }

    public void run() throws Exception {
        // Create csparql engine
        CsparqlEngineImpl engine = new CsparqlEngineImpl();
        engine.initialize(true);

        // Load Static Model
        var staticKnowledge = readModelFromFile("./data/semanticmodel.ttl");
        engine.putStaticNamedModel("http://auto.tuwien.ac.at/example#", staticKnowledge);

        // Connect to MQTT broker
        String serverURI = "tcp://" + config.mqttBroker().host() + ":" + config.mqttBroker().port();
        try (MqttClient mqttClient = new MqttClient(serverURI, config.mqttBroker().clientId())) {
            logger.info("Connecting to MQTT broker...");
            mqttClient.connect();
            logger.info("Connection established.");

            // Connect Stream Reasoning Engine to MQTT broker
            MqttToStreamConnector mqttToStreamSensorConnector = new MqttToStreamConnector(
                    "http://auto.tuwien.ac.at/example#sensor_stream",
                    mqttClient,
                    "events/sensors");
            MqttToStreamConnector mqttToStreamSimpleEventsConnector = new MqttToStreamConnector(
                    "http://auto.tuwien.ac.at/example#simple_events_stream",
                    mqttClient,
                    "events/simple");
            MqttToStreamConnector mqttToStreamComplexEventsConnector = new MqttToStreamConnector(
                    "http://auto.tuwien.ac.at/example#complex_events_stream",
                    mqttClient,
                    "events/complex");

            // Register Streams
            engine.registerStream(mqttToStreamSensorConnector);
            engine.registerStream(mqttToStreamSimpleEventsConnector);
            engine.registerStream(mqttToStreamComplexEventsConnector);

            // Run Query
            CsparqlQueryResultProxy queryDoorOpen = engine.registerQuery(Queries.DETECT_DOOR_OPEN, false);
            queryDoorOpen.addObserver(new StreamToMqttConnector(mqttClient, "events/complex"));

            // Start Streams
            logger.info("Start forwarding MQTT messages to stream reasoning engine...");
            mqttToStreamSensorConnector.startForwarding();
            mqttToStreamSimpleEventsConnector.startForwarding();
            mqttToStreamComplexEventsConnector.startForwarding();

            // Wait for Ctrl+D, if in container, the loop runs forever
            logger.info("Press Ctrl+D to stop...");
            while (System.in.available() == 0
                || System.in.read() != -1) {
                Thread.sleep(1000);
            }

            // Stop forwarding and disconnect
            logger.info("Stopping forwarding MQTT messages to stream reasoning engine...");
            mqttToStreamSensorConnector.stopForwarding();
            mqttToStreamSimpleEventsConnector.stopForwarding();
            mqttToStreamComplexEventsConnector.stopForwarding();
            mqttClient.disconnect();
        }
    }

    private static String readModelFromFile(String path) throws IOException {
        try (InputStream staticKnowledgeFile = FileManager.get().open(path); StringWriter sw = new StringWriter()) {
            Model model = ModelFactory.createDefaultModel();
            model.read(staticKnowledgeFile, (String) null, "TURTLE");
            model.write(sw);
            return sw.toString();
        }
    }
}
