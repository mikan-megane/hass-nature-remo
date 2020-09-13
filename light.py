"""Support for Nature Remo Light."""
import logging

from homeassistant.core import callback
from homeassistant.components.light import (
    LightEntity,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR_TEMP,
    SUPPORT_EFFECT,
    SUPPORT_FLASH,
    SUPPORT_COLOR,
    SUPPORT_TRANSITION,
    SUPPORT_WHITE_VALUE,
)
from . import DOMAIN, NatureRemoBase

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Nature Remo Light."""
    if discovery_info is None:
        return
    _LOGGER.debug("Setting up light platform.")
    coordinator = hass.data[DOMAIN]["coordinator"]
    api = hass.data[DOMAIN]["api"]
    config = hass.data[DOMAIN]["config"]
    appliances = coordinator.data["appliances"]
    async_add_entities(
        [
            NatureRemoLight(coordinator, api, appliance, config)
            for appliance in appliances.values()
            if appliance["type"] == "LIGHT"
        ]
    )


class NatureRemoLight(NatureRemoBase, LightEntity):
    """Implementation of a Nature Remo E sensor."""

    def __init__(self, coordinator, api, appliance, config):
        super().__init__(coordinator, appliance)
        self._api = api
        self._is_on = None
        self._brightness = None
        self._buttons = appliance["light"]["buttons"]
        self._update(appliance["light"]["state"])

    @property
    def supported_features(self):
        # TODO:明るさと白さの操作受付
        return SUPPORT_BRIGHTNESS | SUPPORT_WHITE_VALUE

    @property
    def is_on(self):
        return self._is_on

    @property
    def brightness(self):
        return self._brightness

    @property
    def white_value(self):
        return 125

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        await self._post_name([
            "on",
            "onoff",
        ])

    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        await self._post_name([
            "off",
            "onoff",
        ])

    def _update(self, state, device=None):
        # hold this to determin the ac mode while it's turned-off
        self._is_on = state["power"] == "on"
        self._brightness = int(state["brightness"]) or None

    async def _post_name(self, names):
        all = [x.get("name") for x in self._buttons]
        for name in names:
            if name in all:
                await self._post({"button": name})
                break

    async def _post(self, data):
        response = await self._api.post(
            f"/appliances/{self._appliance_id}/light", data
        )
        self._update(response)
        self.async_write_ha_state()
