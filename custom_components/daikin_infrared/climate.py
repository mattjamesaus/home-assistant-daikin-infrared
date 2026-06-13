"""Climate platform for Daikin Infrared."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    SWING_BOTH,
    SWING_HORIZONTAL,
    SWING_OFF,
    SWING_VERTICAL,
)
from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, CONF_NAME, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_INFRARED_EMITTER_ENTITY_ID,
    CONF_MODEL_PROFILE,
    DEFAULT_NAME,
    DOMAIN,
    MODEL_PROFILES,
)
from .protocol import DaikinClimateState, DaikinCommand

PARALLEL_UPDATES = 1

HA_TO_PROTOCOL_HVAC = {
    HVACMode.COOL: "cool",
    HVACMode.HEAT: "heat",
    HVACMode.HEAT_COOL: "heat_cool",
    HVACMode.DRY: "dry",
    HVACMode.FAN_ONLY: "fan_only",
    HVACMode.OFF: "off",
}

HA_TO_PROTOCOL_FAN = {
    FAN_AUTO: "auto",
    FAN_LOW: "low",
    FAN_MEDIUM: "medium",
    FAN_HIGH: "high",
}

HA_TO_PROTOCOL_SWING = {
    SWING_OFF: "off",
    SWING_VERTICAL: "vertical",
    SWING_HORIZONTAL: "horizontal",
    SWING_BOTH: "both",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Daikin Infrared climate entity from a config entry."""
    async_add_entities([DaikinInfraredClimate(entry)])


class DaikinInfraredClimate(InfraredEmitterConsumerEntity, ClimateEntity, RestoreEntity):
    """Assumed-state Daikin climate entity controlled by infrared."""

    _attr_assumed_state = True
    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 10
    _attr_max_temp = 30
    _attr_target_temperature_step = 1.0
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.HEAT_COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_swing_modes = [
        SWING_OFF,
        SWING_VERTICAL,
        SWING_HORIZONTAL,
        SWING_BOTH,
    ]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the climate entity."""
        data = entry.data
        profile_key = data[CONF_MODEL_PROFILE]
        profile = MODEL_PROFILES[profile_key]

        self._entry = entry
        self._profile_key = profile_key
        self._profile = profile
        self._infrared_emitter_entity_id = data[CONF_INFRARED_EMITTER_ENTITY_ID]
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Daikin",
            model=profile.name,
            name=data.get(CONF_NAME, DEFAULT_NAME),
        )

        self._attr_hvac_mode = HVACMode.OFF
        self._attr_target_temperature = 24.0
        self._attr_fan_mode = FAN_AUTO
        self._attr_swing_mode = SWING_OFF

    async def async_added_to_hass(self) -> None:
        """Restore the last assumed state."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return

        if last_state.state in self.hvac_modes:
            self._attr_hvac_mode = HVACMode(last_state.state)
        if (temperature := last_state.attributes.get(ATTR_TEMPERATURE)) is not None:
            self._attr_target_temperature = float(temperature)
        if (fan_mode := last_state.attributes.get("fan_mode")) in self.fan_modes:
            self._attr_fan_mode = fan_mode
        if (swing_mode := last_state.attributes.get("swing_mode")) in self.swing_modes:
            self._attr_swing_mode = swing_mode

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode and send the full assumed state."""
        self._attr_hvac_mode = hvac_mode
        await self._send_assumed_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature and send the full assumed state."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        self._attr_target_temperature = float(temperature)
        if self.hvac_mode == HVACMode.OFF:
            self._attr_hvac_mode = HVACMode.COOL
        await self._send_assumed_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode and send the full assumed state."""
        self._attr_fan_mode = fan_mode
        await self._send_assumed_state()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set swing mode and send the full assumed state."""
        self._attr_swing_mode = swing_mode
        await self._send_assumed_state()

    async def async_turn_on(self) -> None:
        """Turn the climate entity on using the last non-off state."""
        if self.hvac_mode == HVACMode.OFF:
            self._attr_hvac_mode = HVACMode.COOL
        await self._send_assumed_state()

    async def async_turn_off(self) -> None:
        """Turn the climate entity off."""
        self._attr_hvac_mode = HVACMode.OFF
        await self._send_assumed_state()

    async def _send_assumed_state(self) -> None:
        """Send the current assumed state through the configured emitter."""
        command = DaikinCommand(
            DaikinClimateState(
                hvac_mode=HA_TO_PROTOCOL_HVAC[self.hvac_mode],
                target_temperature=self.target_temperature,
                fan_mode=HA_TO_PROTOCOL_FAN[self.fan_mode],
                swing_mode=HA_TO_PROTOCOL_SWING[self.swing_mode],
            )
        )
        await self._send_command(command)
        self.async_write_ha_state()
