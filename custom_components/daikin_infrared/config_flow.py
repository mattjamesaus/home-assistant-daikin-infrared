"""Config flow for Daikin Infrared."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.infrared import (
    DOMAIN as INFRARED_DOMAIN,
    async_get_emitters,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_INFRARED_EMITTER_ENTITY_ID,
    CONF_MODEL_PROFILE,
    DEFAULT_NAME,
    DOMAIN,
    MODEL_PROFILES,
)


class DaikinInfraredConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Daikin Infrared."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial config step."""
        emitter_entity_ids = async_get_emitters(self.hass)
        if not emitter_entity_ids:
            return self.async_abort(reason="no_emitters")

        if user_input is not None:
            profile = user_input[CONF_MODEL_PROFILE]
            emitter_entity_id = user_input[CONF_INFRARED_EMITTER_ENTITY_ID]
            await self.async_set_unique_id(f"{profile}_{emitter_entity_id}")
            self._abort_if_unique_id_configured()
            title = user_input.get(CONF_NAME) or DEFAULT_NAME
            return self.async_create_entry(title=title, data=user_input)

        profile_options = [
            SelectOptionDict(value=key, label=profile.name)
            for key, profile in MODEL_PROFILES.items()
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MODEL_PROFILE): SelectSelector(
                        SelectSelectorConfig(
                            options=profile_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_INFRARED_EMITTER_ENTITY_ID): EntitySelector(
                        EntitySelectorConfig(
                            domain=INFRARED_DOMAIN,
                            include_entities=emitter_entity_ids,
                        )
                    ),
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                }
            ),
        )

