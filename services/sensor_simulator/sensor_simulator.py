import argparse
import datetime
import logging
import time

from influxdb_client import Point
from lib.timeseries import InfluxDBRepository
from configuration import load_configuration

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Sensor simulation starting...")

    arg_parser = argparse.ArgumentParser(prog="sensor_simulation.py")
    arg_parser.add_argument("-c", "--config", required=True)
    args = arg_parser.parse_args()

    config = load_configuration(args.config)
    timeseries_repository = InfluxDBRepository(config.influxdb)

    logging.info("Waiting for InfluxDB to be ready...")
    timeseries_repository.wait_for_ready()

    logging.info("Waiting for 20 seconds before starting...")
    time.sleep(20)

    """
    The following scenario is simulated by this program. Each point from below is inserted into the
    InfluxDB database with a delay of 3 seconds.

    1) Today is a rather cold autumn day. The outside temperature is approximately 5 degrees Celsius.
       The setpoint temperature and room temperature is set to 23 degrees Celsius. To hold this
       temperature, the heating system controller will set the heater to 15% of its maximum power.

    2) We observe dropping room temperature from 23 to 18 degrees Celsius. This will trigger the
       Room is cold event in the rule-based event detection service.
    
    3) The heating system controller increases the heater power. However, the room temperature is still
       dropping. This will trigger the Power Consumption High event in the model-based event detection
       as the power consumption exceeds the maximum power consumption predicted by the model.
    
    4) The complex event detection will detect that the room is cold and the power consumption is high.
       Furthermore, no events that nullify these events are detected (e.g., room a temp is normal). Thus,
       the complex event "Door might be open" is triggered.
    """

    points = [
        #1)
        Point("room_use_case").field("t_out", 5.0),
        Point("room_use_case").field("t_set", 23.0),
        Point("room_use_case").field("t_a", 23.0),
        Point("room_use_case").field("p_el", 15.0),

        #2)
        Point("room_use_case").field("t_a", 22.0),
        Point("room_use_case").field("t_a", 21.0),
        Point("room_use_case").field("t_a", 20.0),
        Point("room_use_case").field("t_a", 19.0),
        Point("room_use_case").field("t_a", 18.0),

        # If this value is published, the room is no longer cold. Thus, the door open event is not triggered.
        # Point("room_use_case").field("t_a", 21.0), 

        #3)
        Point("room_use_case").field("p_el", 80.0),
    ]

    logging.info("Starting simulation...")
    
    for point in points:
        logging.info(f"Writing point {point}...")
        point.time(datetime.datetime.now(datetime.UTC))
        timeseries_repository.write_point(point)
        time.sleep(3)

    logging.info("Sensor simulation completed...")
