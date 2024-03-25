package at.ac.tuwien.auto.complexevents.configuration;

public record EventDetectorConfig(MqttConfig mqttBroker, String staticModelPath) {
}
