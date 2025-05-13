#!/usr/bin/env python3

import time
import logging
import signal
from pymavlink import mavutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/mavlink_node.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MAVLinkNode:
    def __init__(self):
        logger.info("Initializing MAVLink Node...")

        self.SYSTEM_ID = 1
        self.COMPONENT_ID = 25  # MAV_COMP_ID_USER1

        # Create a simple Mavlink connection with udpout
        self.master = mavutil.mavlink_connection(
            'udpout:localhost:14551',
            source_system=self.SYSTEM_ID,
            source_component=self.COMPONENT_ID,
            dialect='common'
        )

        # Define supported commands and their IDs
        self.commands = {
            "CMD_START_SCAN": 1,  # Command ID for CMD_START_SCAN
            "CMD_OTHER_COMMAND": 2  # Placeholder for other commands
        }

        self.state = mavutil.mavlink.MAV_STATE_STANDBY  # Initial state
        logger.info(f"MAVLink Node initialized (System ID: {self.SYSTEM_ID}," +
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

    def send_heartbeat(self):
        """Send periodic heartbeat message with specific IDs"""
        try:
            self.master.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GENERIC,
                mavutil.mavlink.MAV_COMP_ID_USER1,
                1,  # base_mode
                0,  # custom_mode
                self.state,
                2   # Mavlink version
            )
            logger.info(f"Heartbeat sent (System ID: {self.SYSTEM_ID}," +
                        f" Component ID: {self.COMPONENT_ID}," +
                        f" State: {self.state})")
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")

    def send_statustext(self, text):
        """Send status text message"""
        try:
            self.master.mav.statustext_send(
                mavutil.mavlink.MAV_SEVERITY_INFO,
                text.encode('utf-8')  # Encode text to bytes
            )
            logger.info(f"Status sent: {text}")
        except Exception as e:
            logger.error(f"Error sending status: {e}")

    def handle_command(self, msg):
        """Handle incoming COMMAND_LONG messages"""
        logger.info(f"Received command ID: {msg.command}")

        scan_types = {
            1: "Radar",
            2: "LiDAR",
            3: "Sonar"
        }

        try:
            # Set result based on supported commands
            if msg.command == self.commands["CMD_START_SCAN"]:
                if self.state == mavutil.mavlink.MAV_STATE_STANDBY and msg.param2 in scan_types:
                    result = mavutil.mavlink.MAV_RESULT_ACCEPTED
                else:
                    result = mavutil.mavlink.MAV_RESULT_TEMPORARILY_REJECTED
            else:
                result = mavutil.mavlink.MAV_RESULT_UNSUPPORTED

            # Send command acknowledgment
            self.master.mav.command_ack_send(msg.command, result)
            logger.info(f"Sent command acknowledgment with result: {result}")

            # Handle specific command actions once acknowledgement is sent
            if msg.command == self.commands["CMD_START_SCAN"]:
                scan_type = scan_types.get(msg.param2)
                scan_duration = int(msg.param1)

                # Check if the scan type is supported and if the node is in standby state
                if self.state == mavutil.mavlink.MAV_STATE_STANDBY and scan_type != "Unknown":
                    self.state = mavutil.mavlink.MAV_STATE_ACTIVE
                    self.send_statustext(f"State changed to: {self.state}")

                    # Simulate scan process for the specified duration
                    for i in range(scan_duration):
                        logger.info(f"Scanning... {i+1}/{scan_duration}")
                        self.send_statustext(f"Performing scan type: {scan_type}, State remains: {self.state}")
                        # In a real scenario, this would send telemetry data from the scan to the GCS
                        time.sleep(1)

                    # After scan finished, change state back to standby
                    self.state = mavutil.mavlink.MAV_STATE_STANDBY
                    self.send_statustext(f"State changed to: {self.state}")
                else:
                    self.send_statustext("Scan type not supported or already scanning.")
                    logger.info("Scan type not supported or already scanning.")

        except Exception as e:
            logger.error(f"Error handling command: {e}")

    def run(self):
        """Main loop that sends heartbeats and processes incoming messages"""
        logger.info("MAVLink node running...")
        try:
            while True:
                self.send_heartbeat()

                # Check for incoming messages
                msg = self.master.recv_match(blocking=False)
                if msg:
                    if msg.get_type() == "COMMAND_LONG":
                        self.handle_command(msg)

                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down MAVLink node...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    node = MAVLinkNode()
    node.run()
