"""Sensor setup for tetraconnect integration."""

import logging
from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)

from .const import DOMAIN
# from .entities.connection import ConnectionStatusSensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Callable[[list[Any]], None],
) -> None:
    """Set up tetraconnect sensors based on a config entry."""
    coordinator = hass.data[DOMAIN]

    # Create connection status sensor
    connection_sensor = ConnectionStatusSensor(coordinator)
    async_add_entities([connection_sensor])


class ConnectionStatusSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for connection status in tetraconnect integration."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator) -> None:
        """Initialize the connection status sensor."""
        super().__init__(coordinator)

        cfg = coordinator.config_entry.data
        self._manufacturer = cfg.get("manufacturer", "unknown")
        self._device_id = cfg.get("device_id", "unknown")
        self._model = cfg.get("model", "unknown")
        self._revision = cfg.get("revision", "unknown")

        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_name = "Connection Status"
        self._attr_unique_id = f"connection_status_{self._device_id}"
        self._attr_should_poll = False
        self._current_status = None

        self._attr_device_info = {
            "identifiers": {
                ("tetraconnect", f"{self._manufacturer}_{self._device_id}")
            },
            "name": f"{self._manufacturer} {self._device_id}",
            "manufacturer": self._manufacturer,
            "model": self._model,
            "sw_version": self._revision,
        }

        # Initialize with current data if available
        _LOGGER.debug(
            "Initializing ConnectionStatusSensor with coordinator.data: %s",
            coordinator.data,
        )
        self._update_from_coordinator_data()
        _LOGGER.debug(
            "After init: is_on=%s, icon=%s",
            self.is_on,
            self._attr_icon,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True

    @property
    def is_on(self) -> bool:
        """Return True if connected, False otherwise."""
        return self._current_status == "connected"

    def _update_from_coordinator_data(self) -> None:
        """Update entity attributes from coordinator data."""
        if self.coordinator.data is None:
            _LOGGER.debug("Coordinator data is None, setting disconnected")
            self._current_status = "disconnected"
            self._attr_icon = "mdi:lan-disconnect"
            return

        if "connection_status" in self.coordinator.data:
            status_data = self.coordinator.data.get("connection_status", {})
            status = status_data.get("connection_status", "disconnected")
            self._current_status = status

            # Update icon based on status
            if status == "connected":
                self._attr_icon = "mdi:lan-connect"
            else:
                # reconnecting and disconnected both show as not connected
                self._attr_icon = "mdi:lan-disconnect"
        else:
            _LOGGER.warning("No connection_status in coordinator.data")
            self._current_status = "disconnected"
            self._attr_icon = "mdi:lan-disconnect"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Coordinator update received. Data: %s", self.coordinator.data)
        self._update_from_coordinator_data()
        self.async_write_ha_state()
