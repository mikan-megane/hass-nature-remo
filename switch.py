"""Support for Nature Remo Switch."""
import logging

from homeassistant.core import callback
from homeassistant.components.switch import (
    SwitchEntity,
)
from . import DOMAIN, NatureRemoBase

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Nature Remo Switch."""
    if discovery_info is None:
        return
    _LOGGER.debug("Setting up switch platform.")
    coordinator = hass.data[DOMAIN]["coordinator"]
    api = hass.data[DOMAIN]["api"]
    config = hass.data[DOMAIN]["config"]
    appliances = coordinator.data["appliances"]
    async_add_entities(
        [
            NatureRemoSwitch(coordinator, api, appliance, config)
            for appliance in appliances.values()
            if appliance["type"] == "IR"
        ]
    )


class NatureRemoSwitch(NatureRemoBase, SwitchEntity):
    """Implementation of a Nature Remo E sensor."""

    def __init__(self, coordinator, api, appliance, config):
        super().__init__(coordinator, appliance)
        self._signals = appliance["signals"]
        self._api = api
        self._is_on = False

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        await self._post_icon([
            "ico_on",
        ])
        self._is_on = True

    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        await self._post_icon([
            "ico_off",
            "ico_on",
        ])
        self._is_on = False

    async def _post_icon(self, names):
        images = [x.get("image") for x in self._signals]
        for name in names:
            if name in images:
                await self._post(self._signals[images.index(name)]["id"])
                break

    async def _post(self, signal):
        response = await self._api.post(
            f"/signals/{signal}/send", {}
        )
