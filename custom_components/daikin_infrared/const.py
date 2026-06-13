"""Constants for Daikin Infrared."""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "daikin_infrared"

CONF_INFRARED_EMITTER_ENTITY_ID = "infrared_emitter_entity_id"
CONF_MODEL_PROFILE = "model_profile"

DEFAULT_NAME = "Kitchen Living Daikin"
DEFAULT_MODEL_PROFILE = "daikin_xl_arc466a16"


@dataclass(frozen=True)
class ModelProfile:
    """Supported Daikin infrared model profile."""

    name: str
    indoor_models: tuple[str, ...]
    remote_models: tuple[str, ...]


MODEL_PROFILES = {
    DEFAULT_MODEL_PROFILE: ModelProfile(
        name="Daikin XL / ARC466A16",
        indoor_models=("FTXV85LVMA", "FTXV95LVMA"),
        remote_models=("ARC466A16", "ARC466A14"),
    )
}

