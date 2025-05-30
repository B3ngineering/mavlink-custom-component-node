# mavlink-custom-component-node


## Problem Breakdown

The objective of this solution is to develop a MAVLink node that emulates a custom component (like a sensor) in a MAVLink system that receives and responds to commands. In this case, the assumption is made that the component is a generic telemetry sensor that scans its environment and sends relevant data back to the ground control station.

### Requirements

- Unique component identity, in this case with MAV_TYPE_GENERIC and heartbeat messages with the components ID.
- The node should subscribe to incoming COMMAND_LONG message types and be able to handle and acknowledge these commands.
- Implement a CMD_START_SCAN command with duration and type within COMMAND_LONG
- Broadcast status updates periodically with STATUSTEXT.

## Instructions

### Setup
- Clone this repository to your machine using ``` git clone ```.
- Create a virtual environment with Python in the root directory of the repository using ``` python -m venv <venv> ``` and ``` source <venv>/bin/activate ```.
- Run ``` pip install -r requirements.txt ``` to download the required dependencies.

### Usage

**Development**:
- From the root directory of this repository, start two terminal shells and activate the virtual environment from setup in each.
- In one, run ``` python src/mavlink_node.py ``` and in the other run ``` python src/cli_gcs.py ```.
- Heartbeat message should be picked up by the gcs. 
- Follow the command instructions on the terminal. Inputting a # will call a scan of that duration, and you will then be prompted to select a type of scan. After hitting Enter, the command will be sent.
- The scan will take place in the node and status messages will be sent between the components as state changes, with constant data from the scan for additional information.
- Heartbeat messages should be being received by the gcs from the node at all times.
- After scanning, the user can have another scan take place or try a different command.
- ``` src/send_message.py ``` was also used during prototyping as a simple way to send commands and view responses outside of the command line.

**Testing**:
- Run ``` python tests/run_tests.py ``` from the root directory.
- Observe test suite successes/failures.

## Tools Used

- **Python** was selected as the language of choice for this project due to its extensive documentation, easy-to-use test tools, and rapid prototyping capabilities.
- **pymavlink** was used for handling MAVLink messaging as the specific library to use with Python.
- **UDP** communication was selected over TCP due to its usefulness in real-time applications as well as ease of implementation.
- **unittest** was the test tooling of choice due to its accessibility and ability to quickly assess the functionality of individual components.
- The common **MAVLink 2.0** dialect was selected due to its current support and implementation of all the required messages for this application. Custom CMD_START_SCAN was implemented as a type of COMMAND_LONG.
- State is tracked using MAV_STATE with MAV_STATE_ACTIVE (4) for scanning in progress and MAV_STATE_STANDBY (3) for inactive.

## Proof of Functionality
- The system registers the MAVLink node (``` src/mavlink_node.py ```) as a generic component and transmits heartbeat messages at 1s intervals with its unique user id.
- The MAVLink node subscribes to incoming COMMAND_LONG messages and handles the CMD_START_SCAN command (and sends acknowledgements for each received command).
- Periodically broadcasts status updates when state is changed.
- Uses a CLI tool to simulate a GCS and send COMMAND_LONG messages to the node.
- See sample logs in the logs folder (``` ground_station.log ``` and ``` mavlink_node.log ```). The former includes the user inputs that produced the given logs.

## System Diagram

![alt text](system_diagram.png)

A simple block diagram to illustrate the control flow of the application.

## Features
- Clean shutdown of udp connections when program exits.
- Test tooling for specific features using unittest as well as integration testing for communication between scripts using mocking.

## Potential Next Steps
- Simulate scan results and send data back using status or telemetry.
- Implement additional COMMAND_LONG message support.
- Integrate custom MAVLink messages with common.xml
