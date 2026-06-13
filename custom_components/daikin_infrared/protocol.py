"""Daikin ARC infrared protocol generation.

This module intentionally has no Home Assistant imports so it can be tested
locally without a Home Assistant test harness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, NamedTuple

DAIKIN_IR_FREQUENCY = 38_000

DAIKIN_ARC_PRE_MARK = 9_950
DAIKIN_ARC_PRE_SPACE = 25_100
HEADER_MARK = 3_450
HEADER_SPACE = 1_760
BIT_MARK = 400
ONE_SPACE = 1_300
ZERO_SPACE = 480
MESSAGE_SPACE = 35_000

TEMP_MIN = 10.0
TEMP_MAX = 30.0

MODE_AUTO = 0x00
MODE_COOL = 0x30
MODE_HEAT = 0x40
MODE_DRY = 0x20
MODE_FAN = 0x60
MODE_OFF = 0x00
MODE_ON = 0x01

FAN_AUTO = 0xA0
FAN_LOW = 0x30
FAN_MEDIUM = 0x50
FAN_HIGH = 0x70

HVAC_MODE_BYTES = {
    "cool": MODE_COOL,
    "heat": MODE_HEAT,
    "heat_cool": MODE_AUTO,
    "dry": MODE_DRY,
    "fan_only": MODE_FAN,
}

FAN_MODE_BYTES = {
    "auto": FAN_AUTO,
    "low": FAN_LOW,
    "medium": FAN_MEDIUM,
    "high": FAN_HIGH,
}

SWING_BITS = {
    "off": (0x00, 0x00),
    "vertical": (0x0F, 0x00),
    "horizontal": (0x00, 0x0F),
    "both": (0x0F, 0x0F),
}


@dataclass(frozen=True)
class DaikinClimateState:
    """Assumed Daikin climate state used to generate a full IR command."""

    hvac_mode: str = "cool"
    target_temperature: float = 24.0
    fan_mode: str = "auto"
    swing_mode: str = "off"


class DaikinArcFrames(NamedTuple):
    """Generated Daikin ARC header and state frames."""

    header: bytes
    state: bytes


class DaikinArcCommand:
    """Home Assistant infrared command for a Daikin ARC state."""

    modulation = DAIKIN_IR_FREQUENCY
    repeat_count = 0

    def __init__(self, state: DaikinClimateState) -> None:
        """Initialize the command from an assumed climate state."""
        self.state = state

    def get_raw_timings(self) -> list[int]:
        """Return signed mark/space timings in microseconds."""
        return build_arc_timings(self.state)


def build_arc_frames(state: DaikinClimateState) -> DaikinArcFrames:
    """Build the two Daikin ARC frames for the provided climate state."""
    header = bytearray(
        [
            0x11,
            0xDA,
            0x27,
            0x00,
            0x02,
            0xD0,
            0x02,
            0x03,
            0x80,
            0x03,
            0x82,
            0x30,
            0x41,
            0x1F,
            0x82,
            0xF4,
            0x00,
            0x24,
            0x00,
            0x00,
        ]
    )

    state_frame = bytearray(
        [
            0x11,
            0xDA,
            0x27,
            0x00,
            0x00,
            _operation_mode_byte(state.hvac_mode) | 0x08,
            _temperature_byte(state.hvac_mode, state.target_temperature),
            0x00,
            0x00,
            0x00,
            0x00,
            0x06,
            0x60,
            0x00,
            0x0A,
            0xC4,
            0x80,
            0x24,
            0x00,
        ]
    )

    fan_high_nibble, swing_low_byte = _fan_swing_bytes(
        state.fan_mode, state.swing_mode
    )
    state_frame[8] = fan_high_nibble
    state_frame[9] = swing_low_byte

    header[-1] = _checksum(header[:-1])
    state_frame[-1] = _checksum(state_frame[:-1])
    return DaikinArcFrames(bytes(header), bytes(state_frame))


def build_arc_timings(state: DaikinClimateState) -> list[int]:
    """Build signed Home Assistant infrared timings for a Daikin ARC state."""
    frames = build_arc_frames(state)
    timings = [DAIKIN_ARC_PRE_MARK, -DAIKIN_ARC_PRE_SPACE]
    timings.extend(_frame_timings(frames.header))
    timings.append(BIT_MARK)
    timings.append(-MESSAGE_SPACE)
    timings.extend(_frame_timings(frames.state))
    timings.append(BIT_MARK)
    return timings


def _operation_mode_byte(hvac_mode: str) -> int:
    """Return the Daikin mode byte for an HVAC mode string."""
    if hvac_mode == "off":
        return MODE_OFF
    return HVAC_MODE_BYTES[hvac_mode] | MODE_ON


def _temperature_byte(hvac_mode: str, target_temperature: float) -> int:
    """Return Daikin's temperature byte for the HVAC mode."""
    if hvac_mode in ("dry", "heat_cool"):
        return 0xC0
    if hvac_mode == "fan_only":
        return 0x32

    temperature = min(max(float(target_temperature), TEMP_MIN), TEMP_MAX)
    whole_degrees = int(temperature)
    half_degree_bit = 1 if temperature - whole_degrees >= 0.5 else 0
    return whole_degrees << 1 | half_degree_bit


def _fan_swing_bytes(fan_mode: str, swing_mode: str) -> tuple[int, int]:
    """Return bytes that encode fan and swing state."""
    vertical_bits, horizontal_bits = SWING_BITS[swing_mode]
    return FAN_MODE_BYTES[fan_mode] | vertical_bits, horizontal_bits


def _frame_timings(frame: Iterable[int]) -> list[int]:
    """Convert bytes to signed LSB-first Daikin mark/space timings."""
    timings = [HEADER_MARK, -HEADER_SPACE]
    for byte in frame:
        for bit in range(8):
            timings.append(BIT_MARK)
            if byte & (1 << bit):
                timings.append(-ONE_SPACE)
            else:
                timings.append(-ZERO_SPACE)
    return timings


def _checksum(frame: Iterable[int]) -> int:
    """Return Daikin's one-byte additive checksum."""
    return sum(frame) & 0xFF

