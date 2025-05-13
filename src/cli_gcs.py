#!/usr/bin/env python3

import time
import logging
import signal
from pymavlink import mavutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ground_station.log'),
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
        self.connection.close()
        logger.info("Shut down complete.")
        exit(0)

    def wait_heartbeat(self):
        """Wait for a heartbeat message from the system"""
        logger.info("Waiting for heartbeat...")
        try:
            msg = self.connection.wait_heartbeat(timeout=10)
            if msg:
                logger.info(f"Heartbeat received (System ID: {msg.get_srcSystem()}, " +
                            f"Component ID: {msg.get_srcComponent()}, " + 
                            f"State: {msg.system_status})")
                return True
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False

    def send_scan_command(self, scan_duration=5, scan_type=1):
        """Send CMD_START_SCAN command"""
        try:
            logger.info("Sending CMD_START_SCAN command...")
            self.connection.mav.command_long_send(
                self.connection.target_system,
                self.connection.target_component,
                self.commands["CMD_START_SCAN"],
                0,  # confirmation
                scan_duration,  # param1 (duration of scan in seconds)
                scan_type,  # param2 (type of scan to perform)
                0, 0, 0, 0, 0  # parameters (not used)
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
                msg = self.connection.recv_match(
                    type=['COMMAND_ACK', 'STATUSTEXT', 'HEARTBEAT'],
                    blocking=True,
                    timeout=0)

                if msg is None:
                    continue

                if msg.get_type() == 'COMMAND_ACK':
                    result_map = {
                        mavutil.mavlink.MAV_RESULT_ACCEPTED: "ACCEPTED",
                        mavutil.mavlink.MAV_RESULT_TEMPORARILY_REJECTED: "TEMPORARILY_REJECTED",
                        mavutil.mavlink.MAV_RESULT_DENIED: "DENIED",
                        mavutil.mavlink.MAV_RESULT_UNSUPPORTED: "UNSUPPORTED",
                        mavutil.mavlink.MAV_RESULT_FAILED: "FAILED"
                    }
                    result = result_map.get(msg.result)
                    logger.info(f"Command {msg.command} acknowledgement received: {result}")
                    if result != "ACCEPTED":
                        break
                elif msg.get_type() == 'STATUSTEXT':
                    logger.info(f"Status: {msg.text}")
                elif msg.get_type() == 'HEARTBEAT':
                    logger.info(f"Heartbeat received (System ID: {msg.get_srcSystem()}, " +
                            f"Component ID: {msg.get_srcComponent()}, " + 
                            f"State: {msg.system_status})")

            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                break

    def run(self):
        """Main operation loop for sending commands and monitoring messages"""
        logger.info("Ground Station is running...")
        if not self.wait_heartbeat():  # Wait for first heartbeat before sending commands
            logger.error("No heartbeat received, exiting...")
            return

        logger.info("Heartbeat received, you can start sending commands.")
        try:
            while True:
                # Check if alive
                # Display command options
                command = input("\nCommands:"
                                "\nh: Check hearbeat "
                                "\n#: Send CMD_START_SCAN lasting for # seconds"
                                "\nq: Quit\nEnter command: ")
                if command.isdigit():
                    # User must provide scan type after duration
                    scan_type = input("Enter scan type (1: Radar, 2: LiDAR, 3: Sonar): ")
                    if scan_type in ['1', '2', '3']:
                        if self.send_scan_command(float(command), int(scan_type)):
                            self.monitor_messages(float(command) + 1)  # Monitor for the duration of the scan with buffer
                    else:
                        logger.warning("Invalid scan type. Please enter 1, 2, or 3.")
                elif command.lower() == 'h':
                    self.wait_heartbeat()
                elif command.lower() == 'q':
                    logger.info("Exiting Ground Station...")
                    self.shutdown(None, None)
                else:
                    logger.warning("Invalid command. Please try again.")

        except KeyboardInterrupt:
            logger.info("Shutting down Ground Station...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    gcs = GroundStation()
    gcs.run()
