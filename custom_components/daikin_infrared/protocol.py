"""Daikin infrared protocol generation.

This module intentionally has no Home Assistant imports so it can be tested
locally without a Home Assistant test harness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, NamedTuple

DAIKIN_IR_FREQUENCY = 38_000

HEADER_MARK = 3_360
HEADER_SPACE = 1_760
BIT_MARK = 520
ONE_SPACE = 1_370
ZERO_SPACE = 360
PREAMBLE_SPACE = 26_800
MESSAGE_SPACE = 37_150
END_SPACE = 200_000

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
    power_on: bool = True
    target_temperature: float = 24.0
    fan_mode: str = "low"
    swing_mode: str = "off"


class DaikinFrames(NamedTuple):
    """Generated Daikin frames."""

    frame1: bytes
    frame2: bytes
    frame3: bytes


class DaikinCommand:
    """Home Assistant infrared command for a Daikin state."""

    modulation = DAIKIN_IR_FREQUENCY
    repeat_count = 0

    def __init__(self, state: DaikinClimateState) -> None:
        """Initialize the command from an assumed climate state."""
        self.state = state

    def get_raw_timings(self) -> list[int]:
        """Return signed mark/space timings in microseconds."""
        return build_daikin_timings(self.state)


def build_daikin_frames(state: DaikinClimateState) -> DaikinFrames:
    """Build the three Daikin frames for the provided climate state."""
    frame1 = bytes([0x11, 0xDA, 0x27, 0x00, 0xC5, 0x10, 0x00, 0xE7])
    frame2 = bytes([0x11, 0xDA, 0x27, 0x00, 0x42, 0xFC, 0x24, 0x74])
    frame3 = bytearray(
        [
            0x11,
            0xDA,
            0x27,
            0x00,
            0x00,
            _operation_mode_byte(state.hvac_mode, state.power_on),
            _temperature_byte(state.hvac_mode, state.target_temperature),
            0x00,
            0x00,
            0x00,
            0x00,
            0x06,
            0x60,
            0x20,
            0x00,
            0xC1,
            0x82,
            0x00,
            0x00,
        ]
    )

    fan_high_byte, swing_low_byte = _fan_swing_bytes(state.fan_mode, state.swing_mode)
    frame3[8] = fan_high_byte
    frame3[9] = swing_low_byte
    frame3[-1] = _checksum(frame3[:-1])

    return DaikinFrames(frame1=frame1, frame2=frame2, frame3=bytes(frame3))


def build_daikin_timings(state: DaikinClimateState) -> list[int]:
    """Build signed Home Assistant infrared timings for a Daikin state."""
    frames = build_daikin_frames(state)
    timings = _preamble_timings()
    timings.extend(_frame_timings(frames.frame1))
    timings.append(-MESSAGE_SPACE)
    timings.extend(_frame_timings(frames.frame2))
    timings.append(-MESSAGE_SPACE)
    timings.extend(_frame_timings(frames.frame3))
    timings.append(-END_SPACE)
    return timings


def _operation_mode_byte(hvac_mode: str, power_on: bool) -> int:
    """Return the Daikin mode byte for an HVAC mode string."""
    mode_byte = HVAC_MODE_BYTES[hvac_mode] | 0x08
    if power_on:
        mode_byte |= MODE_ON
    return mode_byte


def _temperature_byte(hvac_mode: str, target_temperature: float) -> int:
    """Return Daikin's temperature byte for the HVAC mode."""
    if hvac_mode == "fan_only":
        return 0x32
    if hvac_mode == "dry":
        return 0xC0

    temperature = min(max(float(target_temperature), TEMP_MIN), TEMP_MAX)
    return round(temperature) << 1


def _fan_swing_bytes(fan_mode: str, swing_mode: str) -> tuple[int, int]:
    """Return bytes that encode fan and swing state."""
    vertical_bits, horizontal_bits = SWING_BITS[swing_mode]
    return FAN_MODE_BYTES[fan_mode] | vertical_bits, horizontal_bits


def _frame_timings(frame: Iterable[int]) -> list[int]:
    """Convert bytes to signed LSB-first Daikin mark/space timings."""
    timings = [HEADER_MARK, -HEADER_SPACE]
    timings.append(BIT_MARK)
    for byte in frame:
        for bit in range(8):
            if byte & (1 << bit):
                timings.append(-ONE_SPACE)
            else:
                timings.append(-ZERO_SPACE)
            timings.append(BIT_MARK)
    return timings


def _preamble_timings() -> list[int]:
    """Return the Daikin ARC466 preamble before the first frame."""
    timings = [BIT_MARK]
    for _ in range(5):
        timings.append(-ZERO_SPACE)
        timings.append(BIT_MARK)
    timings.append(-PREAMBLE_SPACE)
    return timings


def _checksum(frame: Iterable[int]) -> int:
    """Return Daikin's one-byte additive checksum."""
    return sum(frame) & 0xFF
