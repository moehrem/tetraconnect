"""Event firing for tetraconnect integration."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .const import EVENT_CONNECTION_CHANGED, EVENT_ERROR, EVENT_MESSAGE_RECEIVED

_LOGGER = logging.getLogger(__name__)


def fire_message_received(
    hass: HomeAssistant,
    message: dict[str, Any],
) -> None:
    """Fire event when TETRA message is decoded."""

    hass.bus.fire(
        EVENT_MESSAGE_RECEIVED,
        event_data={
            **message,
        },
    )

    _LOGGER.debug("Fired event: %s", EVENT_MESSAGE_RECEIVED)


def fire_error(
    hass: HomeAssistant,
    error_messages: dict[str, Any],
) -> None:
    """Fire event when decoding error occurs."""

    hass.bus.fire(
        EVENT_ERROR,
        event_data={
            **error_messages,
        },
    )

    _LOGGER.warning(
        "Fired event: %s",
        EVENT_ERROR,
    )


def fire_connection_changed(
    hass: HomeAssistant,
    status: str,
) -> None:
    """Fire event when connection status changes."""

    hass.bus.fire(
        EVENT_CONNECTION_CHANGED,
        event_data={
            "status": status,
        },
    )

    _LOGGER.info("Connection status changed: %s", status)
