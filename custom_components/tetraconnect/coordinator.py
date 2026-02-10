"""Coordinator for tetraconnect integration."""

from dataclasses import dataclass, field
import importlib
import logging

import serial

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .com_manager import COMManager
from .const import DOMAIN
from .data_handler import TetraConnectDataHandler
from .helpers import TetraconnectHelpers

_LOGGER = logging.getLogger(__name__)


@dataclass
class PersistentBuffer:
    """Persistent state across multiple handle_serial_data calls."""

    raw_data: bytes = b""


@dataclass
class WorkingBuffer:
    """Encapsulates all state during processing."""

    raw_messages: list[str] = field(default_factory=list)
    decoded_data: str = field(default_factory=str)
    complete_messages: list[str] = field(default_factory=list)
    incomplete_messages: list[str] = field(default_factory=list)
    invalid_messages: list[str] = field(default_factory=list)
    complete_entities: dict[str, dict] = field(default_factory=dict)
    invalid_entities: dict[str, dict] = field(default_factory=dict)


class TetraconnectCoordinator(DataUpdateCoordinator):
    """Coordinator to manage COM data for tetraconnect."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass, _LOGGER, name=f"{DOMAIN} Coordinator", update_interval=None
        )

        self.manufacturer: str = config_entry.data["manufacturer"]
        self.serial_port: str = config_entry.data["serial_port"]
        self.baudrate: int = config_entry.data["baudrate"]

        # init buffers
        self.persistent_buffer = PersistentBuffer()
        self.working_buffer = WorkingBuffer()

        self.helpers = TetraconnectHelpers(self)
        self.handler_module = None  # to be set in async_setup_handlers
        self.data_handler = TetraConnectDataHandler(self)

        self.com_manager = COMManager(self, self.serial_port, self.baudrate)

        # Initialize coordinator data with default connection status
        self.async_set_updated_data(
            {
                "connection_status": {
                    "connection_status": "disconnected",
                    "validity": "valid",
                }
            }
        )

    async def async_setup_handlers(self):
        """Set up necessary handlers."""
        self.handler_module = await self.helpers.get_manufacturer_handler(
            self.manufacturer
        )  # init manufacturer handler for this specific device only

    async def async_start(self):
        """Start the COM manager."""
        try:
            await self.com_manager.serial_initialize(self.hass)
            # await self.com_manager.tetra_initialize()
        except (serial.SerialException, OSError) as e:
            _LOGGER.error("Failed to initialize COM manager: %s", e)
            raise ConfigEntryNotReady from e

    async def async_stop(self):
        """Stop the COM manager."""
        await self.com_manager.serial_stop()

    def handle_serial_data(self, raw_data: bytes) -> None:
        """Handle incoming serial data.

        initializes working buffer, adds new raw data and calls data handler.

        Incoming data is very most likely fragmented, so we need to
        accumulate it in the persistent buffer and process it in chunks.
        Basic rule: the incoming stream is no message!

        """

        # Reset working buffer fields instead of creating a new object
        # This ensures that aliases (self.wb in DataHandler) stay valid
        self.working_buffer.raw_messages = []
        self.working_buffer.decoded_data = ""
        self.working_buffer.complete_messages = []
        self.working_buffer.incomplete_messages = []
        self.working_buffer.invalid_messages = []
        self.working_buffer.complete_entities = {}
        self.working_buffer.invalid_entities = {}

        self.persistent_buffer.raw_data += raw_data
        self.data_handler.data_handler()
