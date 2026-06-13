#!/usr/bin/env python3
"""Decode Broadlink-learned Daikin captures into protocol blocks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from broadlink.remote import data_to_pulses


def _between(value: int, low: int, high: int) -> bool:
    return low <= value <= high


def _expect(pulses: list[int], index: int, low: int, high: int, label: str) -> int:
    value = pulses[index]
    if not _between(value, low, high):
        raise ValueError(f"{label}: expected {low}-{high}, got {value} at {index}")
    return index + 1


def _parse_byte(pulses: list[int], index: int) -> tuple[int, int]:
    value = 0
    for bit in range(8):
        space = pulses[index]
        index += 1
        if _between(space, 950, 1700):
            value |= 1 << bit
        elif not _between(space, 180, 750):
            raise ValueError(f"bad bit space {space} at {index - 1}")
        index = _expect(pulses, index, 250, 800, "bit mark")
    return index, value


def decode_packet(packet: bytes) -> tuple[list[int], list[list[int]]]:
    """Decode a learned Broadlink packet into pulse durations and Daikin blocks."""
    pulses = data_to_pulses(packet)
    index = 0
    index = _expect(pulses, index, 250, 800, "preamble mark")
    for _ in range(5):
        index = _expect(pulses, index, 180, 750, "preamble zero")
        index = _expect(pulses, index, 250, 800, "preamble mark")
    index = _expect(pulses, index, 20000, 28000, "preamble long space")

    blocks: list[list[int]] = []
    for block_len in (8, 8, 19):
        index = _expect(pulses, index, 2800, 4300, "header mark")
        index = _expect(pulses, index, 1400, 2200, "header space")
        index = _expect(pulses, index, 250, 800, "first bit mark")
        block = []
        for _ in range(block_len):
            index, byte = _parse_byte(pulses, index)
            block.append(byte)
        blocks.append(block)
        if block_len != 19:
            index = _expect(pulses, index, 30000, 41000, "interblock space")

    return pulses, blocks


def _format_block(block: list[int]) -> str:
    return " ".join(f"{byte:02X}" for byte in block)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", nargs="+", type=Path)
    return parser.parse_args()


def main() -> int:
    """Decode learned capture files."""
    args = parse_args()
    for path in args.captures:
        payload = json.loads(path.read_text(encoding="utf-8"))
        pulses, blocks = decode_packet(bytes.fromhex(payload["raw_packet_hex"]))
        print(path.name)
        print(f"  pulses: {len(pulses)} total_ms={sum(pulses) / 1000:.3f}")
        for index, block in enumerate(blocks, 1):
            checksum_ok = (sum(block[:-1]) & 0xFF) == block[-1]
            print(f"  block{index}: {_format_block(block)} checksum_ok={checksum_ok}")
        state = blocks[2]
        print(
            "  state:"
            f" mode_power={state[5]:02X}"
            f" temp={state[6] >> 1}"
            f" fan={state[8]:02X}"
            f" swing_h={state[9]:02X}"
            f" b0d={state[13]:02X}"
            f" b0f={state[15]:02X}"
            f" b10={state[16]:02X}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
