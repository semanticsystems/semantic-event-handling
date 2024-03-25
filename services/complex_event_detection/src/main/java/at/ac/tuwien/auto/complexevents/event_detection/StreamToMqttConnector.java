package at.ac.tuwien.auto.complexevents.event_detection;

import java.io.StringWriter;
import java.util.Observable;

import org.apache.jena.riot.Lang;
import org.apache.log4j.Logger;
import org.eclipse.paho.client.mqttv3.MqttClient;
import com.hp.hpl.jena.datatypes.RDFDatatype;
import com.hp.hpl.jena.datatypes.xsd.impl.XSDDateTimeType;
import com.hp.hpl.jena.rdf.model.Model;
import com.hp.hpl.jena.rdf.model.Property;
import com.hp.hpl.jena.rdf.model.RDFNode;
import com.hp.hpl.jena.rdf.model.Resource;
import com.hp.hpl.jena.rdf.model.Statement;

import eu.larkc.csparql.common.RDFTable;
import eu.larkc.csparql.common.RDFTuple;
import eu.larkc.csparql.core.ResultFormatter;

/**
 * This class is responsible for connecting the stream reasoning engine
 * to the MQTT broker. To do so, the class publishes the received
 * quadruples to the given topic after striping the timestamp.
 */
public class StreamToMqttConnector extends ResultFormatter {
    private static final Logger logger = Logger.getLogger(StreamToMqttConnector.class);

    MqttClient mqttClient;
    String topic;

    public StreamToMqttConnector(MqttClient mqttClient, String topic) {
        this.mqttClient = mqttClient;
        this.topic = topic;
    }

    @Override
    public void update(Observable observable, Object rdfTableObject) {
        RDFTable rdfTable = (RDFTable) rdfTableObject;

        // Iterate over all quadruples in the RDF table
        Model model = SenseModel.createModel();
        for (RDFTuple q : rdfTable) {
            Statement statement = createStatementFromTuple(model, q);
            model.add(statement);
        }

        if (model.isEmpty())
            return;

        // Publish the quadruple to the MQTT topic
        try (StringWriter streamWriter = new StringWriter()) {
            model.write(streamWriter, Lang.TTL.getName());
            mqttClient.publish(topic, streamWriter.toString().getBytes(), 0, false);
        } catch (Exception e) {
            logger.error("Error while publishing triple to MQTT topic", e);
        }
    }

    /**
     * Unfortunately, the RDFTable only provides a string representation of the
     * subject, predicate and object. This causes issues because the object
     * could be a literal or a resource. Therefore, we need to parse the
     * string representation of the tuple to a Jena Statement. In the future,
     * we may forward the string representation of the RDFTuple to the MQTT
     * broker directly. However, this may cause interoperability issues as
     * the messages now come from different frameworks.
     */
    private Statement createStatementFromTuple(Model model, RDFTuple tuple) {
        // Parse the subject
        Resource subject = model.createResource(tuple.get(0));
        Property predicate = model.createProperty(tuple.get(1));
        RDFNode object = createObject(model, tuple);
        return model.createStatement(subject, predicate, object);
    }

    private RDFNode createObject(Model model, RDFTuple tuple) {
        if (!tuple.get(2).contains("^^")) {
            return model.createResource(tuple.get(2));
        }

        // Split the object into the literal and the datatype
        String[] parts = tuple.get(2).split("\\^\\^");
        String partOneWithoutQuotes = parts[0].substring(1, parts[0].length() - 1);

        // Obtain the datatype from the string representation
        RDFDatatype datatype = switch (parts[1]) {
            case "http://www.w3.org/2001/XMLSchema#dateTime" -> new XSDDateTimeType("dateTime");
            default -> throw new RuntimeException("Unknown datatype: " + parts[1]);
        };

        return model.createTypedLiteral(partOneWithoutQuotes, datatype);
    }
}
