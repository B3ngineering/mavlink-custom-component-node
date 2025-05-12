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
mock_mavutil.mavlink.MAV_RESULT_ACCEPTED = 0
mock_mavutil.mavlink.MAV_RESULT_UNSUPPORTED = 2
mock_mavutil.mavlink.MAV_TYPE_GENERIC = 0
mock_mavutil.mavlink.MAV_STATE_ACTIVE = 4

# Patch mavutil before importing MAVLinkNode
sys.modules['mavutil'] = mock_mavutil
sys.modules['pymavlink.mavutil'] = mock_mavutil

from src.mavlink_node import MAVLinkNode


class TestMAVLinkNode(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.node = MAVLinkNode()
        self.node.master = Mock()

    def test_initialization(self):
        """Test proper initialization of the MAVLink node."""
        self.assertEqual(self.node.SYSTEM_ID, 1)
        self.assertEqual(self.node.COMPONENT_ID, 25)
        self.assertEqual(self.node.state, "IDLE")

    def test_send_heartbeat(self):
        """Test heartbeat message sending."""
        self.node.send_heartbeat()
        self.node.master.mav.heartbeat_send.assert_called_once_with(
            mock_mavutil.mavlink.MAV_TYPE_GENERIC,
            mock_mavutil.mavlink.MAV_COMP_ID_USER1,
            1,
            0,
            mock_mavutil.mavlink.MAV_STATE_ACTIVE,
            2   # Mavlink version
        )

    def test_handle_command_start_scan(self):
        """Test handling of START_SCAN command."""
        mock_msg = Mock()
        mock_msg.command = 1  # START_SCAN command
        mock_msg.param1 = 3  # 3 seconds duration

        self.node.handle_command(mock_msg)
        self.node.master.mav.command_ack_send.assert_called_once()
        self.assertEqual(self.node.state, "IDLE")

    def test_handle_unsupported_command(self):
        """Test handling of unsupported command."""
        mock_msg = Mock()
        mock_msg.command = 999  # Unsupported command

        self.node.handle_command(mock_msg)
        self.node.master.mav.command_ack_send.assert_called_once_with(
            mock_msg.command,
            mock_mavutil.mavlink.MAV_RESULT_UNSUPPORTED
        )


if __name__ == '__main__':
    unittest.main()
