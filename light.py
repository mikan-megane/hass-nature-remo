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
        self._last_button = None
        self._buttons = appliance["light"]["buttons"]
        self._update(appliance["light"]["state"])

    @property
    def supported_features(self):
        # TODO:明るさと白さの操作受付
        return SUPPORT_BRIGHTNESS | SUPPORT_WHITE_VALUE

    @property
    def is_on(self):
        return self._last_button != "onoff"

    @property
    def brightness(self):
        if self._last_button == "onoff":
            return 0
        elif self._last_button == "on-100":
            return 255
        elif self._last_button == "night":
            return 1
        else:
            return 125

    @property
    def white_value(self):
        return 125

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        if "brightness" in kwargs:
            brightness = kwargs["brightness"]
            if brightness < 20:
                await self._post_name(["night"])
            elif brightness == 255:
                await self._post_name(["on-100"])
            elif brightness < 125:
                await self._post_name(["bright-down"])
            elif brightness >= 125:
                await self._post_name(["bright-up"])
        elif "white_value" in kwargs:
            white_value = kwargs["white_value"]
            if white_value < 125:
                await self._post_name(["colortemp-down"])
            elif white_value >= 125:
                await self._post_name(["colortemp-up"])
        else:
            await self._post_name([
                "on",
                "onoff",
            ])

    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        _LOGGER.debug(kwargs)
        await self._post_name([
            "off",
            "onoff",
        ])

    def _update(self, state, device=None):
        # hold this to determin the ac mode while it's turned-off
        self._last_button = state["last_button"] or None

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
