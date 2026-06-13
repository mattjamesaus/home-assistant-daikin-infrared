#!/usr/bin/env python3
"""Learn an IR command directly from a Broadlink remote.

This tool bypasses Home Assistant. It puts the Broadlink into IR learning mode,
waits for one physical remote button press, and saves the learned Broadlink
packet plus decoded pulse durations for protocol comparison.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import broadlink
    from broadlink import exceptions as broadlink_exceptions
    from broadlink.remote import data_to_pulses
except ImportError:  # pragma: no cover - exercised by manual use.
    broadlink = None
    broadlink_exceptions = None
    data_to_pulses = None


def learned_packet_summary(packet: bytes) -> dict[str, Any]:
    """Return a compact summary for a learned Broadlink packet."""
    pulses = data_to_pulses(packet)
    return {
        "packet_length": len(packet),
        "packet_sha256": hashlib.sha256(packet).hexdigest(),
        "pulse_count": len(pulses),
        "total_duration_ms": round(sum(pulses) / 1000, 3),
        "first_pulses_us": pulses[:40],
        "last_pulses_us": pulses[-20:],
    }


def capture_ir(host: str, port: int, timeout: float, poll_interval: float) -> bytes:
    """Capture one IR command from a Broadlink device."""
    if broadlink is None or broadlink_exceptions is None:
        raise RuntimeError("Install broadlink first: .venv/bin/python -m pip install broadlink")

    device = broadlink.hello(host, port=port, timeout=int(timeout))
    device.auth()
    device.enter_learning()

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            packet = device.check_data()
        except broadlink_exceptions.StorageError:
            packet = b""

        if packet:
            return bytes(packet)
        time.sleep(poll_interval)

    raise TimeoutError(f"No IR command captured within {timeout:.1f}s")


def write_capture(output_dir: Path, host: str, packet: bytes) -> Path:
    """Write a learned packet capture as JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(timezone.utc).isoformat()
    summary = learned_packet_summary(packet)
    payload = {
        "captured_at": captured_at,
        "host": host,
        "raw_packet_hex": packet.hex(),
        **summary,
    }
    filename = f"broadlink-{captured_at.replace(':', '-').replace('+', 'Z')}.json"
    path = output_dir / filename
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="192.168.2.110", help="Broadlink IP address")
    parser.add_argument("--port", default=80, type=int, help="Broadlink port")
    parser.add_argument("--timeout", default=25.0, type=float, help="Seconds to wait")
    parser.add_argument("--poll-interval", default=0.4, type=float, help="Polling seconds")
    parser.add_argument(
        "--output-dir",
        default="captures",
        type=Path,
        help="Directory for learned packet JSON files",
    )
    return parser.parse_args()


def main() -> int:
    """Run the learning workflow."""
    args = parse_args()
    print(f"Connecting to Broadlink at {args.host}:{args.port}...")
    print("Entering IR learn mode. Point the Daikin remote at the Broadlink and press one button.")

    try:
        packet = capture_ir(args.host, args.port, args.timeout, args.poll_interval)
    except Exception as err:
        print(f"Capture failed: {err}", file=sys.stderr)
        return 1

    path = write_capture(args.output_dir, args.host, packet)
    summary = learned_packet_summary(packet)
    print(f"Captured packet: {path}")
    print(f"Packet length: {summary['packet_length']} bytes")
    print(f"Pulse count: {summary['pulse_count']}")
    print(f"Total duration: {summary['total_duration_ms']} ms")
    print(f"SHA256: {summary['packet_sha256']}")
    print(f"First pulses: {summary['first_pulses_us']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

