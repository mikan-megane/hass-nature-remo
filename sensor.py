"""Support for Nature Remo E energy sensor."""
import logging

from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    ENERGY_KILO_WATT_HOUR,
    # PERCENTAGE,
    POWER_WATT,
    TEMP_CELSIUS,
)
from homeassistant.helpers.entity import Entity
from . import DOMAIN, NatureRemoBase

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Nature Remo E sensor."""
    if discovery_info is None:
        return
    _LOGGER.debug("Setting up sensor platform.")
    coordinator = hass.data[DOMAIN]["coordinator"]
    appliances = coordinator.data["appliances"]
    devices = coordinator.data["devices"]
    async_add_entities(
        [
            NatureRemoE(coordinator, appliance)
            for appliance in appliances.values()
            if appliance["type"] == "EL_SMART_METER"
        ]
    )
    async_add_entities(
        [
            NatureRemoSensor(coordinator, device, "illuminate", "lm", DEVICE_CLASS_ILLUMINANCE, "il")
            for device in devices
            if "newest_events" in device
        ]
    )
    async_add_entities(
        [
            NatureRemoSensor(coordinator, device, "temperature", TEMP_CELSIUS, DEVICE_CLASS_TEMPERATURE, "te")
            for device in devices
            if "newest_events" in device
        ]
    )
    async_add_entities(
        [
            NatureRemoSensor(coordinator, device, "humidity", "%", DEVICE_CLASS_HUMIDITY, "hu")
            for device in devices
            if "newest_events" in device
        ]
    )


class NatureRemoE(NatureRemoBase):
    """Implementation of a Nature Remo E sensor."""

    def __init__(self, coordinator, appliance):
        super().__init__(coordinator, appliance)
        self._unit_of_measurement = POWER_WATT

    @property
    def state(self):
        """Return the state of the sensor."""
        appliance = self._coordinator.data["appliances"][self._appliance_id]
        smart_meter = appliance["smart_meter"]
        echonetlite_properties = smart_meter["echonetlite_properties"]
        measured_instantaneous = next(
            value["val"] for value in echonetlite_properties if value["epc"] == 231
        )
        _LOGGER.debug("Current state: %sW", measured_instantaneous)
        return measured_instantaneous

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_POWER

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update the entity.

        Only used by the generic entity update service.
        """
        await self._coordinator.async_request_refresh()


class NatureRemoSensor(Entity):
    """Implementation of a Nature Remo E sensor."""
    # TODO:何故か登録されない件

    def __init__(self, coordinator, device, type_name, unit, device_class, type_id):
        _LOGGER.debug(type_name)
        self._coordinator = coordinator
        self._device = device
        self._name = f"Nature Remo {device['name']} {type_name}"
        self._appliance_id = f"{device['id']}-{type_name}"
        self._unit_of_measurement = unit
        self._device_class = device_class
        self._type_id = type_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._appliance_id

    @property
    def should_poll(self):
        """Return the polling requirement of the entity."""
        return False

    @property
    def device_info(self):
        """Return the device info for the sensor."""
        # Since device registration requires Config Entries, this dosen't work for now
        return {
            "identifiers": {(DOMAIN, self._device["id"])},
            "name": self._device["name"],
            "manufacturer": "Nature Remo",
            "model": self._device["serial_number"],
            "sw_version": self._device["firmware_version"],
        }

    @property
    def state(self):
        """Return the state of the sensor."""
        measured_instantaneous = self._device["newest_events"][self._type_id]["val"]
        _LOGGER.debug("Current state: %s", measured_instantaneous)
        return measured_instantaneous

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update the entity.

        Only used by the generic entity update service.
        """
        await self._coordinator.async_request_refresh()
