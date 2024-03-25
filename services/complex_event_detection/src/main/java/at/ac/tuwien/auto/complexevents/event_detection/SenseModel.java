package at.ac.tuwien.auto.complexevents.event_detection;

import com.hp.hpl.jena.rdf.model.Model;
import com.hp.hpl.jena.rdf.model.ModelFactory;

public class SenseModel {
    public static Model createModel() {
        Model model = ModelFactory.createDefaultModel();
        model.setNsPrefix("xsd", "http://www.w3.org/2001/XMLSchema#");
        model.setNsPrefix("s", "http://w3id.org/explainability/");
        model.setNsPrefix("ex", "http://auto.tuwien.ac.at/example#");
        model.setNsPrefix("sosa", "http://www.w3.org/ns/sosa/");
        return model;
    }
}
