#!/usr/bin/env python3
"""Send generated Daikin IR directly through a Broadlink remote.

This bypasses Home Assistant for protocol diagnostics. It defaults to dry-run
mode and only transmits when `--send` is provided.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

try:
    import broadlink
    from broadlink.remote import data_to_pulses, pulses_to_data
except ImportError:  # pragma: no cover - exercised by manual use.
    broadlink = None
    data_to_pulses = None
    pulses_to_data = None

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from custom_components.daikin_infrared.protocol import (
    DaikinClimateState,
    build_daikin_frames,
    build_daikin_timings,
)


def broadlink_packet_for_state(state: DaikinClimateState) -> bytes:
    """Build a Broadlink packet for a Daikin climate state."""
    timings = build_daikin_timings(state)
    pulses = [abs(timing) for timing in timings]
    return pulses_to_data(pulses)


def packet_summary(packet: bytes) -> dict[str, Any]:
    """Return a compact summary for a Broadlink packet."""
    pulses = data_to_pulses(packet)
    return {
        "packet_length": len(packet),
        "packet_sha256": hashlib.sha256(packet).hexdigest(),
        "pulse_count": len(pulses),
        "total_duration_ms": round(sum(pulses) / 1000, 3),
        "first_pulses_us": pulses[:40],
        "last_pulses_us": pulses[-20:],
    }


def send_packet(host: str, port: int, timeout: int, packet: bytes) -> None:
    """Send a Broadlink packet to the device."""
    if broadlink is None:
        raise RuntimeError("Install broadlink first: .venv/bin/python -m pip install broadlink")

    device = broadlink.hello(host, port=port, timeout=timeout)
    device.auth()
    device.send_data(packet)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="192.168.2.110", help="Broadlink IP address")
    parser.add_argument("--port", default=80, type=int, help="Broadlink port")
    parser.add_argument("--timeout", default=5, type=int, help="Network timeout seconds")
    parser.add_argument("--mode", default="cool", choices=["cool", "heat", "heat_cool", "dry", "fan_only"])
    parser.add_argument("--temp", default=23, type=float, help="Target temperature")
    parser.add_argument(
        "--fan",
        default="speed_1",
        choices=[
            "speed_1",
            "speed_2",
            "speed_3",
            "speed_4",
            "speed_5",
            "auto",
            "quiet",
            "low",
            "medium",
            "high",
            "night",
        ],
    )
    parser.add_argument("--swing", default="off", choices=["off", "vertical", "horizontal", "both"])
    parser.add_argument("--off", action="store_true", help="Send power off while preserving mode")
    parser.add_argument("--send", action="store_true", help="Actually transmit IR")
    return parser.parse_args()


def main() -> int:
    """Build, summarize, and optionally transmit one Daikin command."""
    args = parse_args()
    state = DaikinClimateState(
        hvac_mode=args.mode,
        power_on=not args.off,
        target_temperature=args.temp,
        fan_mode=args.fan,
        swing_mode=args.swing,
    )
    frames = build_daikin_frames(state)
    packet = broadlink_packet_for_state(state)
    summary = packet_summary(packet)

    print(
        "State:"
        f" mode={state.hvac_mode}"
        f" power_on={state.power_on}"
        f" temp={state.target_temperature:g}"
        f" fan={state.fan_mode}"
        f" swing={state.swing_mode}"
    )
    for index, frame in enumerate(frames, 1):
        print(f"Frame {index}: {' '.join(f'{byte:02X}' for byte in frame)}")
    print(f"Packet length: {summary['packet_length']} bytes")
    print(f"Pulse count: {summary['pulse_count']}")
    print(f"Total duration: {summary['total_duration_ms']} ms")
    print(f"SHA256: {summary['packet_sha256']}")

    if not args.send:
        print("Dry run only. Add --send to transmit IR.")
        return 0

    try:
        send_packet(args.host, args.port, args.timeout, packet)
    except Exception as err:
        print(f"Send failed: {err}", file=sys.stderr)
        return 1

    print(f"Sent IR through Broadlink at {args.host}:{args.port}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
