#!/usr/bin/env python3

import time
import socket
import logging
import signal
from pymavlink import mavutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GroundStation:
    def __init__(self):
        logger.info("Initializing Ground Station...")

        self.SYSTEM_ID = 255      # GCS system ID
        self.COMPONENT_ID = 26   # MAV_COMP_ID_USER2

        # Create a simple MAVLink connection with udpin
        self.connection = mavutil.mavlink_connection(
            'udpin:localhost:14551',
            source_system=self.SYSTEM_ID,
            source_component=self.COMPONENT_ID,
            input=True,
            bind=True,
            dialect='common'
        )

        # Define supported commands and their IDs
        self.commands = {
            "CMD_START_SCAN": 1  # Command ID for CMD_START_SCAN
        }

        logger.info(f"Ground Station initialized (System ID: {self.SYSTEM_ID}," +
                    f"Component ID: {self.COMPONENT_ID})")

        # Register signal handlers for proper shutdown
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        """Handle shutdown signals by closing the connection"""
        logger.info("Shutting down...")
        self.master.close()
        logger.info("Shut down complete.")
        exit(0)

    def wait_heartbeat(self):
        """Wait for a heartbeat message from the system"""
        logger.info("Waiting for heartbeat...")
        try:
            msg = self.connection.wait_heartbeat(timeout=10)
            if msg:
                logger.info(f"Heartbeat received from system {self.connection.target_system}" +
                            " component {self.connection.target_component}")
                return True
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False

    def send_scan_command(self, time=5.0):
        """Send CMD_START_SCAN command"""
        try:
            logger.info("Sending CMD_START_SCAN command...")
            self.connection.mav.command_long_send(
                self.connection.target_system,
                self.connection.target_component,
                self.commands["CMD_START_SCAN"],
                0,  # confirmation
                time,  # param1 (duration of scan in seconds)
                0, 0, 0, 0, 0, 0  # parameters (not used)
            )
            return True
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False

    def monitor_messages(self, timeout=10):
        """Monitor for incoming messages"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                msg = self.connection.recv_match(blocking=True, timeout=1)
                if msg:
                    if msg.get_type() == 'COMMAND_ACK':
                        logger.info(f"Received acknowledgment for command {msg.command}")
                        logger.info(f"Result: {msg.result}")
                    elif msg.get_type() == 'STATUSTEXT':
                        logger.info(f"Status: {msg.text}")
                    elif msg.get_type() == 'HEARTBEAT':
                        logger.info(f"Heartbeat received from system {msg.get_srcSystem()} "
                                    f"component {msg.get_srcComponent()}")
                    continue
            except socket.error:
                continue

    def run(self):
        """Main operation loop for sending commands and monitoring messages"""
        logger.info("Ground Station is running...")
        self.wait_heartbeat()  # Wait for first heartbeat before sending commands
        logger.info("Heartbeat received, you can start sending commands.")
        try:
            while True:
                command = input("\nCommands:"
                                "\n0: Check hearbeat "
                                "\n#: Send CMD_START_SCAN with that duration"
                                "\nq: Quit\nEnter command: ")
                if command.isdigit():
                    if command == '0':
                        self.wait_heartbeat()
                    elif self.send_scan_command(float(command)):
                        self.monitor_messages()
                else:
                    logger.warning("Invalid command")
        except KeyboardInterrupt:
            logger.info("Shutting down Ground Station...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    gcs = GroundStation()
    gcs.run()
