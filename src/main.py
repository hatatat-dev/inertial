#!/usr/bin/env -S PYTHONPATH=../telemetry python3

from typing import *
from telemetry.config_log import *

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


def sample() -> None:
    """Sample the inertial sensors and log the relative rotations and orientations"""
    try:
        global origin_rotations

        current_rotations: Tuple[float, ...] = tuple(
            inertial.rotation() for inertial in inertials
        )

        if origin_rotations is None:
            origin_rotations = current_rotations

        relative_rotations = tuple(
            current - origin
            for origin, current in zip(origin_rotations, current_rotations)
        )

        orientations = tuple(
            orientation
            for sub in (
                (
                    inertial.orientation(OrientationType.ROLL),
                    inertial.orientation(OrientationType.PITCH),
                    inertial.orientation(OrientationType.YAW),
                )
                for inertial in inertials
            )
            for orientation in sub
        )

        log(
            ("inertial", "inertial"), "sample", "", *(relative_rotations + orientations)
        )

    except Exception as e:
        log(("inertial", "inertial"), "error", str(e))


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
