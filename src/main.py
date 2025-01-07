#!/usr/bin/env -S PYTHONPATH=../telemetry python3

from typing import *
from telemetry.config_log import *
from vex import *

# Open log based on config
config_open_log()

# Flush log every 10 seconds
repeated_event(flush_log, 0, 10000)

INERTIAL_PORTS = [Ports.PORT3, Ports.PORT2]
"""List of ports with inertial sensors"""

inertials = [Inertial(port) for port in INERTIAL_PORTS]
"""List of inertial sensors"""

origin_rotations: Optional[Tuple[float, ...]] = None
"""Original rotation values of the inertial sensors at the first sample"""

ROTATION_SNAP_STEP = 90.0
"""Expect sampling only to happen at these intervals"""

rotation_snap_error: float = 0.0
"""Current error based on the snapped rotation value"""


def sample() -> None:
    """Sample the inertial sensors and log the relative rotations and orientations"""
    global origin_rotations
    global rotation_snap_error

    current_rotations: Tuple[float, ...] = tuple(
        inertial.rotation() for inertial in inertials
    )

    if origin_rotations is None:
        # Capture the first rotations as the origin
        origin_rotations = current_rotations

    # Compute the relative rotations since the origin
    relative_rotations = tuple(
        current - origin for origin, current in zip(origin_rotations, current_rotations)
    )

    # Expect sampling only to happen at these intervals"""
    snapped_rotation = (
        round((relative_rotations[0] + rotation_snap_error) / ROTATION_SNAP_STEP)
        * ROTATION_SNAP_STEP
    )

    # Update the error based on the snapped rotation value
    rotation_snap_error = snapped_rotation - relative_rotations[0]

    # Collect the inertial sensors orientations
    orientations: List[float] = []

    for inertial in inertials:
        for orientation in (
            OrientationType.ROLL,
            OrientationType.PITCH,
            OrientationType.YAW,
        ):
            orientations.append(inertial.orientation(orientation))

    # Log the rotations, starting with the expected snapped value
    timestamp = log(
        ("inertial", "inertial"), "rotations", "", snapped_rotation, *relative_rotations
    )

    # Log the orientations, with a separate log entry, but with the same timestamp
    log_with_timestamp(
        timestamp, ("inertial", "inertial"), "orientations", "", *orientations
    )


# Calibrate the inertial sensors
log(("inertial", "inertial"), "calibrate")

for inertial in inertials:
    inertial.calibrate()

while any(inertial.is_calibrating() for inertial in inertials):
    sleep(100, TimeUnits.MSEC)

log(("inertial", "inertial"), "run")

brain = Brain()

bumper = Bumper(brain.three_wire_port.a)

# Sample the inertial sensors when the bumper is pressed
bumper.pressed(sample)

controller = Controller()

# Also sample the inertial sensors when the A button is pressed
controller.buttonA.pressed(sample)

# Flush the log when the B button is pressed
controller.buttonB.pressed(flush_log)
