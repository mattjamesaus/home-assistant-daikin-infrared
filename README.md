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
- Fan modes: auto, low, medium, high.
- Swing modes: off, vertical, horizontal, both.

## Assumed State

Infrared is one-way in this release. The integration assumes commands were received by the air conditioner after the emitter sends them. If someone uses the physical remote, Home Assistant may show stale state until the next command is sent from Home Assistant.

Receiver-based state sync may be added later if a compatible Home Assistant infrared receiver is configured and reliable Daikin frame parsing is added.

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
