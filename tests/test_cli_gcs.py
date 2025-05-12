#!/usr/bin/env python3

import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

# Ensure consistent test environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create minimal mock mavutil module
mock_mavutil = MagicMock()
mock_mavutil.mavlink_connection = MagicMock()
mock_mavutil.mavlink.MAV_TYPE_GENERIC = 0
mock_mavutil.mavlink.MAV_COMP_ID_USER1 = 25

# Patch mavutil before importing GroundStation
sys.modules['mavutil'] = mock_mavutil
sys.modules['pymavlink.mavutil'] = mock_mavutil

from src.cli_gcs import GroundStation


class TestGroundStation(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures and mock objects."""
        self.gcs = GroundStation()
        self.gcs.connection = Mock()
        self.gcs.connection.target_system = 1
        self.gcs.connection.target_component = 25

    def test_initialization(self):
        """Test proper initialization of the ground station."""
        self.assertEqual(self.gcs.SYSTEM_ID, 255)
        self.assertEqual(self.gcs.COMPONENT_ID, 26)
        self.assertIn("CMD_START_SCAN", self.gcs.commands)

    def test_wait_heartbeat(self):
        """Test heartbeat waiting functionality."""
        # Create a mock heartbeat message with specific system/component IDs
        mock_heartbeat = Mock()
        mock_heartbeat.get_srcSystem.return_value = 1
        mock_heartbeat.get_srcComponent.return_value = 25
        mock_heartbeat.type = mock_mavutil.mavlink.MAV_TYPE_GENERIC

        # Set up the mock to return our heartbeat and update target system/component
        def mock_wait_heartbeat(*args, **kwargs):
            self.gcs.connection.target_system = 1
            self.gcs.connection.target_component = 25
            return mock_heartbeat

        self.gcs.connection.wait_heartbeat.side_effect = mock_wait_heartbeat

        result = self.gcs.wait_heartbeat()

        # Check that the heartbeat was received and the target system/component were set
        self.assertTrue(result)
        self.gcs.connection.wait_heartbeat.assert_called_once_with(timeout=10)
        self.assertEqual(self.gcs.connection.target_system, 1)
        self.assertEqual(self.gcs.connection.target_component, 25)

    def test_send_scan_command(self):
        """Ensure that the scan command is sent correctly."""
        duration = 5.0
        type = 1
        result = self.gcs.send_scan_command(duration)

        self.assertTrue(result)
        self.gcs.connection.mav.command_long_send.assert_called_once_with(
            self.gcs.connection.target_system,
            self.gcs.connection.target_component,
            self.gcs.commands["CMD_START_SCAN"],
            0,
            duration,  # param1
            type, # param2
            0, 0, 0, 0, 0
        )


if __name__ == '__main__':
    unittest.main()
