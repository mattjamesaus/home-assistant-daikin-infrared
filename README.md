# Daikin Infrared for Home Assistant

Custom Home Assistant integration for controlling a Daikin air conditioner through Home Assistant's native `infrared` platform.

This first release is intentionally narrow. It targets a Daikin XL indoor unit such as `FTXV95LVMA` / `FTXV85LVMA` with an `ARC466A16` or closely related `ARC466A14` remote profile, and sends generated three-frame Daikin infrared commands through a selected Home Assistant infrared emitter.

## Requirements

- Home Assistant 2026.4 or newer.
- An `infrared` emitter entity, for example `infrared.kitchen_universal_remote_ir_emitter`.
- HACS for installation as a custom repository.

## Installation

1. Add this repository to HACS as a custom integration repository.
2. Install `Daikin Infrared`.
3. Restart Home Assistant.
4. Go to Settings > Devices & services.
5. Add `Daikin Infrared`.
6. Select:
   - Model profile: `Daikin XL / ARC466A16`
   - Infrared emitter: your local `infrared` emitter entity
   - Name: the display name for the climate entity

## Supported Controls

- HVAC modes: off, cool, heat, heat/cool, dry, fan only.
- Target temperature: 10-30 degrees Celsius in 1 degree steps.
- Fan modes: speed_1, speed_2, speed_3, speed_4, speed_5, auto, quiet.
- Swing modes: off, vertical, horizontal, both.

## Assumed State

Infrared is one-way in this release. The integration assumes commands were received by the air conditioner after the emitter sends them. If someone uses the physical remote, Home Assistant may show stale state until the next command is sent from Home Assistant.

Receiver-based state sync may be added later if a compatible Home Assistant infrared receiver is configured and reliable Daikin frame parsing is added.

## Troubleshooting Response Issues

Daikin IR commands are full-state packets, not tiny button presses. This integration serializes sends and waits at least 1.5 seconds between completed transmissions so quick UI changes do not fire multiple long IR packets back-to-back.

For testing, wait a couple of seconds between changes and start with a simple command such as cool, 23 degrees, fan speed_1. If the emitter flashes but the unit does not beep or respond, the next useful evidence is a captured IR frame from the physical remote for the same setting.

The fan speed values match the Daikin ARC466-style protocol nibble values: `speed_1` through `speed_5`, plus `auto` and `quiet`. Legacy `low`, `medium`, and `high` service values are still accepted as aliases for `speed_1`, `speed_3`, and `speed_5`.

The current protocol bytes and timing preamble are aligned with captures from the local ARC466-style remote learned through the Broadlink RM4 Pro.

The current generated timing packet has been direct-tested through the local Broadlink and confirmed to make the indoor unit respond.

## Development

Set up local tests:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install pytest
.venv/bin/python -m pytest
```

Protocol tests run without Home Assistant:

```bash
.venv/bin/python -m pytest tests/test_protocol.py -q
```

## Design Notes

This integration does not use Broadlink learned-code services. It generates Daikin raw timings and sends them through Home Assistant's `infrared` abstraction, so the same climate entity can work with any emitter implementation that supports Home Assistant's native infrared platform.
