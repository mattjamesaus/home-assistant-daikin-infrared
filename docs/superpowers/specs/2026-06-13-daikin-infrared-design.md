# Daikin Infrared Design

## Goal

Build a HACS-installable Home Assistant custom integration that exposes one assumed-state Daikin climate entity and sends generated Daikin infrared commands through Home Assistant's native `infrared` emitter platform.

## Scope

The first release targets this house's likely setup only:

- Indoor unit: Daikin FTXV95LVMA or closely related XL-series model.
- Remote profile: Daikin XL / ARC466A16.
- Emitter class: any Home Assistant `infrared` emitter, with the local Broadlink RM4 Pro expected to appear as `infrared.kitchen_universal_remote_ir_emitter`.

The integration does not learn Broadlink commands, does not depend on Broadlink services, and treats climate state as assumed unless receiver support is added later.

## Architecture

`protocol.py` is pure Python and has no Home Assistant imports. It builds three-frame Daikin state commands from climate state, computes checksums, and returns signed raw timings compatible with Home Assistant's `infrared` command API.

`config_flow.py` uses Home Assistant infrared helpers to list available emitters and stores the selected model profile, emitter entity ID, and display name. `climate.py` restores assumed state, updates state optimistically after successful sends, and uses Home Assistant's infrared consumer base class to forward commands through the selected emitter.

## Files

- `custom_components/daikin_infrared/protocol.py`: frame and timing generation.
- `custom_components/daikin_infrared/climate.py`: `ClimateEntity` implementation.
- `custom_components/daikin_infrared/config_flow.py`: UI setup flow.
- `custom_components/daikin_infrared/const.py`: domain, option keys, profile definitions.
- `custom_components/daikin_infrared/__init__.py`: config entry setup and unload.
- `custom_components/daikin_infrared/manifest.json`: Home Assistant metadata.
- `custom_components/daikin_infrared/strings.json`: config flow translations.
- `tests/test_protocol.py`: local tests for protocol bytes and timings.
- `README.md`, `hacs.json`, `pyproject.toml`: HACS and development metadata.

## Behavior

The entity supports off, cool, heat, heat/cool, dry, and fan-only modes. It supports target temperature from 10 to 30 degrees Celsius in 1 degree steps, fan auto/low/medium/high, and swing off/vertical/horizontal/both. Unsupported Daikin remote features such as timers, humidity, powerful mode, economy mode, comfort airflow, and receiver-based state sync are intentionally excluded from the first release.

Every user climate change sends a full Daikin state command. If the send succeeds, Home Assistant state is updated optimistically. If the emitter is missing or unavailable, the entity follows the infrared consumer availability behavior and does not claim hardware feedback.

## Testing

Protocol tests verify mode encoding, temperature encoding, fan and swing encoding, checksums, frame lengths, signed timing polarity, and total timing count. Home Assistant runtime behavior is kept small and conventional so the first local verification can run without a full Home Assistant test harness.
