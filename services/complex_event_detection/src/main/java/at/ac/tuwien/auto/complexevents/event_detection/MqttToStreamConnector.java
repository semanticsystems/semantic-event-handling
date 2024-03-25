package at.ac.tuwien.auto.complexevents.event_detection;

import java.io.StringReader;
import java.io.UnsupportedEncodingException;

import org.apache.jena.riot.Lang;
import org.apache.jena.riot.RDFDataMgr;
import org.apache.log4j.Logger;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;

import com.hp.hpl.jena.rdf.model.Model;
import com.hp.hpl.jena.rdf.model.Property;
import com.hp.hpl.jena.rdf.model.RDFNode;
import com.hp.hpl.jena.rdf.model.Resource;
import com.hp.hpl.jena.rdf.model.Statement;
import com.hp.hpl.jena.rdf.model.StmtIterator;

import eu.larkc.csparql.cep.api.RdfQuadruple;
import eu.larkc.csparql.cep.api.RdfStream;

/**
 * This class is responsible for connecting MQTT broker to the stream
 * reasoning engine. To do so, the class registers a listener to a
 * given topic and forwards the received messages to the stream reasoning
 * engine.
 */
public class MqttToStreamConnector extends RdfStream {
    private static final Logger logger = Logger.getLogger(MqttToStreamConnector.class);

    MqttClient mqttClient;
    String topic;

    public MqttToStreamConnector(String streamIRI, MqttClient mqttClient, String topic) {
        super(streamIRI);
        this.mqttClient = mqttClient;
        this.topic = topic;
    }

    public void startForwarding() throws MqttException {
        // Subscribe to the MQTT topic
        mqttClient.subscribe(topic, (topic, msg) -> {
            try {
                handleMqttMessage(msg);
            } catch (Exception e) {
                logger.error("Error while forwarding message to stream reasoning engine", e);
            }
        });
    }

    private void handleMqttMessage(MqttMessage msg) throws UnsupportedEncodingException {
        // Create string from MQTT message
        String message = new String(msg.getPayload(), "UTF-8");

        logger.trace(msg);

        // Parse RDF triples in the message using Jena
        Model model = SenseModel.createModel();
        try (StringReader stringReader = new StringReader(message)) {
            // Use RDFDataMgr to read the Turtle data into the model
            RDFDataMgr.read(model, stringReader, null, Lang.TTL);
        } catch (Exception e) {
            logger.error("Error while parsing RDF triples from MQTT message", e);
            return;
        }

        // Iterate over all triples in the message
        long timestamp = ModelUtilities.obtainEventTimestamp(model);
        StmtIterator iter = model.listStatements();
        while (iter.hasNext()) {
            Statement stmt = iter.nextStatement();
            Resource subject = stmt.getSubject();
            Property predicate = stmt.getPredicate();
            RDFNode object = stmt.getObject();

            // Extend the triples with the timestamp
            RdfQuadruple q = new RdfQuadruple(
                    subject.toString(),
                    predicate.toString(),
                    object.toString(),
                    timestamp);

            logger.trace("Emitted quadruple: " + q);

            // Add quadruple to the stream
            this.put(q);
        }
    }

    public void stopForwarding() throws MqttException {
        // Unsubscribe from the MQTT topic
        mqttClient.unsubscribe(topic);
    }
}
