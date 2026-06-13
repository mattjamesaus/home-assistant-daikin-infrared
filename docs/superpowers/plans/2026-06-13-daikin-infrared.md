# Daikin Infrared Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a HACS-installable Home Assistant Daikin infrared climate integration using Home Assistant's native `infrared` emitter platform.

**Architecture:** The protocol module is pure Python and tested outside Home Assistant. The Home Assistant layer provides config flow, entity setup, assumed climate state, and command dispatch through the selected infrared emitter.

**Tech Stack:** Home Assistant custom integration APIs, Home Assistant 2026.4+ infrared helpers, Python protocol tests with pytest.

---

## File Structure

- `custom_components/daikin_infrared/protocol.py`: pure Daikin bytes and signed timings.
- `custom_components/daikin_infrared/climate.py`: assumed-state ClimateEntity and IR send orchestration.
- `custom_components/daikin_infrared/config_flow.py`: emitter and profile selection.
- `custom_components/daikin_infrared/const.py`: constants and profile data.
- `custom_components/daikin_infrared/__init__.py`: setup and unload.
- `custom_components/daikin_infrared/manifest.json`: HA metadata.
- `custom_components/daikin_infrared/strings.json`: flow strings.
- `tests/test_protocol.py`: protocol-level tests.
- `README.md`, `hacs.json`, `pyproject.toml`: repository metadata.

### Task 1: Protocol Tests

- [ ] Create `tests/test_protocol.py` with tests for default frame bytes, checksum, half-degree temperature encoding, special dry/fan temperature bytes, swing/fan encoding, and signed timing output.
- [ ] Run `python3.11 -m pytest tests/test_protocol.py -q` and confirm the tests fail because `custom_components.daikin_infrared.protocol` does not exist.

### Task 2: Protocol Implementation

- [ ] Create `custom_components/daikin_infrared/protocol.py`.
- [ ] Implement `DaikinClimateState`, `DaikinArcCommand`, frame generation, checksum generation, and signed raw timing generation.
- [ ] Run `python3.11 -m pytest tests/test_protocol.py -q` and confirm all protocol tests pass.

### Task 3: Home Assistant Integration Scaffold

- [ ] Create `const.py`, `manifest.json`, `__init__.py`, `config_flow.py`, `strings.json`, and `climate.py`.
- [ ] Use `infrared.async_get_emitters` in the config flow.
- [ ] Use `InfraredEmitterConsumerEntity` in the climate entity and send `DaikinArcCommand` instances through `_send_command`.

### Task 4: HACS and User Docs

- [ ] Create `README.md`, `hacs.json`, and `pyproject.toml`.
- [ ] Document HACS installation, setup, supported profile, and assumed-state limitations.

### Task 5: Verification

- [ ] Run `python3.11 -m pytest`.
- [ ] Run `python3.11 -m compileall custom_components tests`.
- [ ] Inspect `git diff --check`.
