package at.ac.tuwien.auto.complexevents;

import org.apache.commons.cli.CommandLine;
import org.apache.commons.cli.CommandLineParser;
import org.apache.commons.cli.DefaultParser;
import org.apache.commons.cli.Options;
import org.apache.log4j.Logger;
import org.apache.log4j.PropertyConfigurator;
import com.fasterxml.jackson.databind.ObjectMapper;

import at.ac.tuwien.auto.complexevents.configuration.EventDetectorConfig;
import at.ac.tuwien.auto.complexevents.event_detection.EventDetector;

import java.io.File;

/**
 * This class is the entry point of the application.
 */
public class App {
    private static final Logger logger = Logger.getLogger(App.class);

    public static void main(String[] args) throws Exception {
        // Configure log4j logger for the csparql engine
        PropertyConfigurator.configure("config/log4j.properties");

        // Parse command line arguments
        Options options = createOptions();
        CommandLineParser parser = new DefaultParser();
        CommandLine cmd = parser.parse(options, args);

        // Load event detector configuration
        String configPath = cmd.getOptionValue("config");
        if(configPath == null) {
            logger.error("No configuration file specified");
            System.exit(1);
        }
        File jsonFile = new File(configPath);
        ObjectMapper objectMapper = new ObjectMapper();
        EventDetectorConfig config = objectMapper.readValue(jsonFile, EventDetectorConfig.class);

        // Run Event Detector
        EventDetector eventDetector = new EventDetector(config);
        eventDetector.run();

        logger.info("Bye World!");
    }

    private static Options createOptions() {
        Options options = new Options();
        options.addOption("c", "config", true, "Path to the configuration file");
        return options;
    }
}
