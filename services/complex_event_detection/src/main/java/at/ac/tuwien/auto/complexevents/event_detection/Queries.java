package at.ac.tuwien.auto.complexevents.event_detection;

public class Queries {
    static final String DETECT_DOOR_OPEN = """
REGISTER QUERY DetectOpenDoorQuery AS
PREFIX : <http://auto.tuwien.ac.at/example#>
PREFIX s: <http://w3id.org/explainability/>
PREFIX sosa: <http://www.w3.org/ns/sosa/>
CONSTRUCT {
    :DetectOpenDoorSensor sosa:madeObservation ?newEventObs.
    ?newEventObs a sosa:Observation ;
        sosa:resultTime ?timestamp ;
        sosa:usedProcedure :DetectOpenDoorQuery ;
        sosa:hasResult ?newEvent .
    ?newEvent s:causallyRelated ?roomAColdEvent ;
        s:causallyRelated ?powerConsumptionHighEvent .
}
FROM STREAM <http://auto.tuwien.ac.at/example#sensor_stream> [RANGE 120s STEP 10s]
FROM STREAM <http://auto.tuwien.ac.at/example#simple_events_stream> [RANGE 120s STEP 10s]
FROM STREAM <http://auto.tuwien.ac.at/example#complex_events_stream> [RANGE 120s STEP 10s]
WHERE {
    ?roomAColdEventObs a sosa:Observation ;
        sosa:resultTime ?roomColdTimestamp ;
        sosa:hasResult [ a :RoomAColdEvent ] .
    ?powerConsumptionHighEventObs a sosa:Observation ; 
        sosa:resultTime ?highPowerConsumptionTimestamp ;
        sosa:hasResult [ a :PowerConsumptionHighEvent ] .
    FILTER NOT EXISTS {
        ?roomANormalEventObs a sosa:Observation ;
            sosa:resultTime ?roomATempIsNormalTimestamp ;
            sosa:hasResult [ a :RoomANormalEvent ] .
        FILTER(?roomATempIsNormalTimestamp >= ?roomColdTimestamp)
    }
    FILTER NOT EXISTS {
        ?powerConsumptionNormalEventObs a sosa:Observation ;
            sosa:resultTime ?powerConsumptionNormalTimestamp ;
            sosa:hasResult [ a :PowerConsumptionIsNormalEvent ] .
        FILTER(?powerConsumptionNormalTimestamp >= ?highPowerConsumptionTimestamp)
    }
    FILTER NOT EXISTS {
        ?setPointChangedObs a sosa:Observation ;
            sosa:hasResult [ a :Zone1SetPointChangedEvent ] .
    }
    FILTER NOT EXISTS {
        ?doorOpenObs a sosa:Observation ;
            sosa:hasResult [ a :DoorOpenEvent ] .
    }
    BIND(
        IF(?roomColdTimestamp > ?highPowerConsumptionTimestamp,
            ?roomColdTimestamp,
            ?highPowerConsumptionTimestamp)
        AS ?timestamp
    )
    BIND(REPLACE(STR(?timestamp), "[^0-9]", "") AS ?timestampStr)
    BIND(IRI(CONCAT("http://auto.tuwien.ac.at/example#obs_DoorOpen_", ?timestampStr)) AS ?newEventObs)
    BIND(IRI(CONCAT("http://auto.tuwien.ac.at/example#event_DoorOpen_", ?timestampStr)) AS ?newEvent)
}
""";

    static final String TIMESTAMP_FROM_EVENTS = """
PREFIX sosa: <http://www.w3.org/ns/sosa/>
SELECT ?timestamp
WHERE {
    ?obs sosa:resultTime ?timestamp .
}
""";

}
