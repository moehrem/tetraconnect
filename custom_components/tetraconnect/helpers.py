"""Several unils and tool helping handling of tetraconnect."""

import importlib
import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Factory dictionary mapping manufacturer names to handler classes
# This allows lookup without blocking import_module calls during async initialization
# _MANUFACTURER_HANDLERS = {
#     "motorola": Motorola,
# }


class TetraconnectHelpers:
    """Class for any helper method, that is not needed for a specific purpose only."""

    def __init__(self, coordinator) -> None:
        """Initialize tetraconnectHelpers."""
        self.coordinator = coordinator
        self.hass: HomeAssistant = coordinator.hass

        self.manufacturer = coordinator.manufacturer

    def update_connection_status(self, status):
        """Set connection status."""
        import logging

        logger = logging.getLogger(__name__)

        status_mapping = {
            1: "connected",
            2: "reconnecting",
            3: "disconnected",
        }

        status_text = status_mapping.get(status, "unknown")
        logger.debug(
            "update_connection_status called with status=%d (%s)", status, status_text
        )

        message = {
            "connection_status": {
                "connection_status": status_text,
                "validity": "valid",
            }
        }

        self.coordinator.async_set_updated_data(message)

    async def get_manufacturer_handler(self, manufacturer: str) -> object:
        """Dynamically import and return the manufacturer-specific handler class based on manufacturer name, avoiding blocking the event loop."""

        module_name = f"custom_components.tetraconnect.{manufacturer.lower()}"
        class_name = manufacturer.capitalize()

        def import_handler(manufacturer: str):
            module = importlib.import_module(
                f"custom_components.tetraconnect.{manufacturer}"
            )
            return getattr(module, manufacturer.capitalize())

        try:
            handler_class = await self.hass.async_add_executor_job(
                import_handler, manufacturer.lower()
            )
            self.handler_instance = handler_class(self)
            return self.handler_instance
        except ModuleNotFoundError:
            _LOGGER.error("Manufacturer module not found: %s", module_name)
            self.handler_instance = None
        except AttributeError:
            _LOGGER.error(
                "Handler class '%s' not found in module '%s'", class_name, module_name
            )
            self.handler_instance = None
        except Exception as err:
            _LOGGER.error(
                "Could not instantiate handler class for '%s': %s",
                self.manufacturer,
                err,
            )
            self.handler_instance = None
