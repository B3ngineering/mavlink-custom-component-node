import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

# Ensure consistent test environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create minimal mock mavutil module
mock_mavutil = MagicMock()
mock_mavutil.mavlink_connection = MagicMock()
mock_mavutil.mavlink.MAV_RESULT_ACCEPTED = 0
mock_mavutil.mavlink.MAV_RESULT_UNSUPPORTED = 2
mock_mavutil.mavlink.MAV_TYPE_GENERIC = 0
mock_mavutil.mavlink.MAV_STATE_ACTIVE = 4

# Patch mavutil before importing MAVLinkNode
sys.modules['mavutil'] = mock_mavutil
sys.modules['pymavlink.mavutil'] = mock_mavutil

from src.mavlink_node import MAVLinkNode
from src.cli_gcs import GroundStation


class TestMAVLinkNodeIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for integration tests."""
        self.node = MAVLinkNode()
        self.node.master = Mock()

        self.gcs = GroundStation()
        self.gcs.target_system = self.node.SYSTEM_ID
        self.gcs.target_component = self.node.COMPONENT_ID

    def tearDown(self):
        """Clean up after each test."""
        self.node.master.reset_mock()
        self.gcs.connection = None
        self.node = None
        self.gcs = None

    def test_integration_start_scan(self):
        """Test integration: GroundStation sends CMD_START_SCAN to MAVLinkNode."""
        mock_command = Mock()
        mock_command.command = self.node.commands["CMD_START_SCAN"]
        mock_command.param1 = 3  # Duration of scan
        mock_command.param2 = 1  # Scan type (Radar)

        self.node.handle_command(mock_command)

        self.node.master.mav.command_ack_send.assert_called_once_with(
            mock_command.command,
            mock_mavutil.mavlink.MAV_RESULT_ACCEPTED
        )

    def test_integration_unsupported_command(self):
        """Test integration: GroundStation sends unsupported command to MAVLinkNode."""
        mock_command = Mock()
        mock_command.command = 999  # Unsupported command

        self.node.handle_command(mock_command)

        self.node.master.mav.command_ack_send.assert_called_once_with(
            mock_command.command,
            mock_mavutil.mavlink.MAV_RESULT_UNSUPPORTED
        )

    def test_integration_reject_scan_while_scanning(self):
        """Test integration: GroundStation sends CMD_START_SCAN while MAVLinkNode is already scanning."""
        self.node.state = "SCANNING"

        mock_command = Mock()
        mock_command.command = self.node.commands["CMD_START_SCAN"]
        mock_command.param1 = 3  # Duration of scan
        mock_command.param2 = 1  # Scan type (Radar)

        self.node.handle_command(mock_command)

        self.node.master.mav.command_ack_send.assert_called_once_with(
            mock_command.command,
            mock_mavutil.mavlink.MAV_RESULT_TEMPORARILY_REJECTED
        )

        self.node.master.mav.statustext_send.assert_called_once_with(
            mock_mavutil.mavlink.MAV_SEVERITY_INFO,
            b"Scan type not supported or already scanning."
        )