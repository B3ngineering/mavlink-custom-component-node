#!/usr/bin/env python3

from pymavlink import mavutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def send_command_long(master, target_system, target_component, command, param1=0, param2=0, param3=0, param4=0, param5=0, param6=0, param7=0):
    """
    Sends a COMMAND_LONG message to the MAVLink node.
    """
    try:

        # Wait for a heartbeat to ensure the connection is established
        logger.info("Waiting for heartbeat...")
        master.wait_heartbeat()
        logger.info("Heartbeat received. Sending COMMAND_LONG...")

        # Send the COMMAND_LONG message
        master.mav.command_long_send(
            target_system,        # Target system ID
            target_component,     # Target component ID
            command,              # Command ID
            0,                    # Confirmation (0: First transmission)
            param1, param2, param3, param4, param5, param6, param7
        )
        logger.info(f"COMMAND_LONG sent (Command ID: {command}, Params: {param1}, {param2}, {param3}, {param4}, {param5}, {param6}, {param7})")

    except Exception as e:
        logger.error(f"Error sending COMMAND_LONG: {e}")


if __name__ == "__main__":
    # Define the target system and component IDs
    TARGET_SYSTEM = 1
    TARGET_COMPONENT = 25

    # Define the command and parameters
    COMMAND_ID = 1  # CMD_START_SCAN
    PARAM1 = 5      # Scan duration
    PARAM2 = 1      # Scan type

    # Initialize the connection
    logger.info("Initializing MAVLink connection...")
    master = mavutil.mavlink_connection('udpin:localhost:14551')

    # Send the command
    send_command_long(master, TARGET_SYSTEM, TARGET_COMPONENT, COMMAND_ID, PARAM1, PARAM2)

    # Wait for a response
    while True:
        message = master.recv_match(blocking=True, timeout=10)
        if message:
            logger.info(f"Received message: {message}")
