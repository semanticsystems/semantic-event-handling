package at.ac.tuwien.auto.complexevents.event_detection;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import com.hp.hpl.jena.query.QueryExecutionFactory;
import com.hp.hpl.jena.query.QueryFactory;
import com.hp.hpl.jena.query.ResultSetFormatter;
import com.hp.hpl.jena.rdf.model.Model;

public class ModelUtilities {
    /**
     * Queries the model for the timestamp of the message. If more than
     * one timestamp is found, an exception is thrown.
     */
    public static long obtainEventTimestamp(Model model) {
        var query = QueryFactory.create(Queries.TIMESTAMP_FROM_EVENTS);
        var results = QueryExecutionFactory.create(query, model).execSelect();
        var resultList = ResultSetFormatter.toList(results);

        if (resultList.size() != 1)
            throw new RuntimeException("Expected exactly one timestamp, but got " + resultList.size() + " instead");

        // Return the timestamp
        var timestampString = resultList.get(0).getLiteral("timestamp").getString();
        LocalDateTime timestamp = LocalDateTime.parse(timestampString, DateTimeFormatter.ISO_DATE_TIME);
        long utcTimestamp = timestamp.atZone(ZoneId.of("UTC")).toInstant().toEpochMilli();
        return utcTimestamp;
    }
}
