"""Diagnostics support for tetraconnect integration."""

from __future__ import annotations

import logging
from typing import Any
from pathlib import Path

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr


from .const import DOMAIN, LOG_FILE

_LOGGER = logging.getLogger(__name__)

TO_REDACT: set[str] = {
    "latitude",
    "longitude",
    "lat",
    "lng",
    "issi_sen",
    "issi_rec",
}


def _read_log(hass: HomeAssistant) -> list[str]:
    log_file = Path(hass.config.path(LOG_FILE))

    if not log_file.exists():
        return ["Logfile not found."]

    with log_file.open("r", encoding="utf-8") as file:
        return [line for line in file if "tetraconnect" in line]


async def _read_events_async(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Read tetraconnect events from coordinator buffers.

    The events are accumulated during message processing in the working buffer
    and complete entities are fired as Home Assistant events.
    """
    events_list: list[dict[str, Any]] = []

    try:
        # Get the coordinator directly from hass.data
        if DOMAIN in hass.data:
            coordinator = hass.data[DOMAIN]

            # Check if coordinator has the working buffer with processed entities
            if hasattr(coordinator, "working_buffer"):
                working_buffer = coordinator.working_buffer

                # Collect complete entities (successfully processed messages)
                if (
                    hasattr(working_buffer, "complete_entities")
                    and working_buffer.complete_entities
                ):
                    for (
                        entity_key,
                        entity_data,
                    ) in working_buffer.complete_entities.items():
                        events_list.append(
                            {
                                "type": "complete_message",
                                "entity_id": entity_key,
                                "command": entity_data.get("sds_command", "Unknown"),
                                "command_desc": entity_data.get(
                                    "sds_command_desc", "Unknown"
                                ),
                                "data": {
                                    "sds_type": entity_data.get("sds_type"),
                                    "issi_sen": entity_data.get("issi_sen"),
                                    "issi_rec": entity_data.get("issi_rec"),
                                },
                            }
                        )

                # Collect invalid entities (messages with errors)
                if (
                    hasattr(working_buffer, "invalid_entities")
                    and working_buffer.invalid_entities
                ):
                    for (
                        entity_key,
                        entity_data,
                    ) in working_buffer.invalid_entities.items():
                        events_list.append(
                            {
                                "type": "invalid_message",
                                "entity_id": entity_key,
                                "command": entity_data.get("sds_command", "Unknown"),
                                "command_desc": entity_data.get(
                                    "sds_command_desc", "Unknown"
                                ),
                                "data": entity_data,
                            }
                        )
    except Exception as err:
        _LOGGER.debug("Could not read events from coordinator: %s", err)

    # If no events found, return a note about event logging
    if not events_list:
        events_list.append(
            {
                "note": "No processed events available in current session.",
                "info": "Events are logged to Home Assistant log file as they are processed.",
                "recommendation": "Check home-assistant.log for detailed event history.",
            }
        )

    return events_list


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data: dict[str, Any] = dict(entry.data)
    options: dict[str, Any] = dict(entry.options)

    # Read and filter logs for tetraconnect
    tetraconnect_logs = await hass.async_add_executor_job(_read_log, hass)

    # Read events asynchronously
    events = await _read_events_async(hass)

    return {
        "entry_data": async_redact_data(data, TO_REDACT),
        "options": async_redact_data(options, TO_REDACT),
        "runtime_data": getattr(entry, "runtime_data", None),
        "logs": tetraconnect_logs,
        "event_count": len(events),
        "events": events,
    }


async def async_get_device_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device: dr.DeviceEntry,
) -> dict[str, Any]:
    """Return diagnostics for a device."""

    return {
        "device_details": {
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "revision": device.sw_version,
        },
    }
