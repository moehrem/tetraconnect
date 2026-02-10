"""Config flow to configure the tetraconnect integration."""

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import serial
import serial_asyncio  # type: ignore
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    MANUFACTURERS_LIST,
    VERSION,
    MINOR_VERSION,
    PATCH_VERSION,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class TetraconnectConfigEntry:
    """Data class to hold device information."""

    manufacturer: str = "unknown"
    serial_port: str = ""
    baudrate: int = 0
    device_id: str = "unknown"
    model: str = "unknown"
    revision: str = "unknown"
    # mqtt_enabled: bool = True
    # mqtt_topic: str = MQTT_TOPIC_DEFAULT
    # mqtt_broker: str = (
    #     "localhost"  # Default broker address, can be overridden by user input
    # )


class TetraconnectConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tetraconnect."""

    VERSION = VERSION
    MINOR_VERSION = MINOR_VERSION
    PATCH_VERSION = PATCH_VERSION

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.config_entry = TetraconnectConfigEntry()
        self.errors: dict[str, str] = {}

        # self.mqtt_enabled = True
        # self.mqtt_topic = MQTT_TOPIC_DEFAULT
        # self.mqtt_broker = "localhost"

    async def async_step_user(
        self, user_input: dict[str, object] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step of the config flow."""

        if user_input is not None:
            # init error buffer
            self.errors = {}

            # set user input variables
            self.config_entry.manufacturer = str(user_input["manufacturer"])
            self.config_entry.serial_port = str(user_input["serial_port"])
            self.config_entry.baudrate = int(str(user_input["baudrate"]))
            # self.config_entry.mqtt_enabled = bool(user_input.get("mqtt_enabled"))
            # self.config_entry.mqtt_topic = str(user_input.get("mqtt_topic"))
            # self.config_entry.mqtt_broker = str(user_input.get("mqtt_broker"))

            try:
                await self._request_device_data(self.config_entry)
            except TimeoutError:
                self.errors["base"] = "timeout_error"
                return await self._async_show_form_user()

            except (serial.SerialException, OSError):
                self.errors["base"] = "serial_error"
                return await self._async_show_form_user()

            except ValueError:
                self.errors["base"] = "manufacturer_mismatch"
                return await self._async_show_form_user()

            # try:
            #     if self.config_entry.mqtt_enabled:
            #         await self._check_mqtt_broker(self.config_entry.mqtt_broker)
            # except ValueError as e:
            #     self.errors["base"] = "mqtt_broker_error"
            #     _LOGGER.error("MQTT broker check failed: %s", e)
            #     return await self._async_show_form_user()

            # create config entry
            return self.async_create_entry(
                title=f"{self.config_entry.manufacturer} {self.config_entry.device_id}",
                data=self.config_entry.__dict__,
            )

        return await self._async_show_form_user()

    async def _async_show_form_user(self) -> ConfigFlowResult:
        """Show the user input form."""

        ports = await self.hass.async_add_executor_job(self._get_serial_ports)

        # Default values for first form display
        if hasattr(self, "hass") and hasattr(self.hass, "data"):
            user_input = getattr(self, "user_input", None)
        else:
            user_input = None

        # Try to get previous user input if available
        if user_input is None:
            user_input = {}
        # self.mqtt_enabled = user_input.get("mqtt_enabled", self.mqtt_enabled)
        # self.mqtt_topic = user_input.get("topic", self.mqtt_topic)

        schema_dict = {
            vol.Required("manufacturer"): vol.In(MANUFACTURERS_LIST),
            vol.Required("serial_port"): vol.In(ports),
            vol.Required("baudrate", default=38400): vol.All(
                vol.Coerce(int), vol.Range(min=300, max=115200)
            ),
            # vol.Optional("mqtt_enabled", default=True): bool,
        }
        # if self.mqtt_enabled:
        #     schema_dict[vol.Required("mqtt_broker", default=self.mqtt_broker)] = str

        #     schema_dict[vol.Required("mqtt_topic", default=self.mqtt_topic)] = str

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema_dict),
            errors=self.errors,
        )

    def _get_serial_ports(self) -> list[str]:
        """Return a filtered list of usable serial ports on the system."""
        devices: list[str] = []

        # patterns to match serial devices
        serial_patterns = [
            "/dev/ttyUSB*",
            "/dev/ttyACM*",
            "/dev/ttyS*",
            "/dev/ttyAMA*",
            "/dev/serial/by-id/*",
            "/dev/pts/[0-9]*",
        ]

        # check each pattern and collect devices
        for pattern in serial_patterns:
            devices.extend(str(p) for p in Path("/").glob(pattern.lstrip("/")))

        # filter devices that are readable and writable
        usable_devices = [
            dev
            for dev in devices
            if Path(dev).exists() and os.access(dev, os.R_OK | os.W_OK)
        ]

        return sorted(set(usable_devices))

    async def _request_device_data(self, config_entry: TetraconnectConfigEntry):
        """Request serial port and request device data.

        Request manufacturer, model and revision identification from the device.
        Wait for an answer for each command.
        This will not create any entities, its just for device setup.

        Service commands will be initialized in com_manager.

        """
        device_commands = [
            "ATZ\r\n",
            "AT+GMI?\r\n",
            "AT+GMM?\r\n",
            "AT+GMR?\r\n",
        ]

        try:
            reader, writer = await asyncio.wait_for(
                serial_asyncio.open_serial_connection(
                    url=config_entry.serial_port, baudrate=config_entry.baudrate
                ),
                timeout=5,
            )
        except (serial.SerialException, OSError) as e:
            raise ConfigEntryNotReady(
                f"Failed to connect to serial port {config_entry.serial_port}: {e}"
            ) from e

        # send initial commands to the device
        for cmd in device_commands:
            writer.write(cmd.encode("utf-8"))
            await asyncio.sleep(0.1)

        await writer.drain()
        response = b""
        response = await asyncio.wait_for(reader.read(1024), timeout=5)

        writer.close()
        await writer.wait_closed()

        # parse response
        self._parse_init_data(response)

    def _parse_init_data(self, response) -> None:
        """Parse the initial response to extract manufacturer, and device ID."""

        device_manufacturer = "Unknown"
        device_id = "Unknown"
        device_revision = "Unknown"

        response = response.decode("utf-8").strip()
        _LOGGER.debug("Config: Raw response: %s", response)

        response_lines = response.split("\r\n")

        for line in response_lines:
            if line.startswith("+GMI") and ":" in line:
                device_manufacturer = line.split(":", 1)[1].strip()
                self._check_manufacturer(device_manufacturer)
            elif line.startswith("+GMM") and ":" in line:
                parts = line.split(":", 1)[1].strip().split(",")
                if len(parts) > 1:
                    device_id = parts[1]
            elif line.startswith("+GMR") and ":" in line:
                device_revision = line.split(":", 1)[1].strip()
            # elif line.startswith("AT+CTSP"):
            #     message = line.split(":", 1)
            #     if message[1].strip() != "OK":
            #         _LOGGER.warning(
            #             "Service profile command %s failed with response: %s",
            #             line,
            #             message[1].strip(),
            #         )

        self.config_entry.model = device_id
        self.config_entry.device_id = device_id
        self.config_entry.revision = device_revision

    def _check_manufacturer(self, manufacturer: str):
        """Check if the user manufacturer matches the device manufacturer."""

        device_manufacturer = manufacturer.strip().lower()
        user_manufacturer = self.config_entry.manufacturer.strip().lower()

        if device_manufacturer.lower() != user_manufacturer.lower():
            _LOGGER.error(
                "Manufacturer mismatch! device confirms: %s, user has entered: %s",
                device_manufacturer,
                user_manufacturer,
            )
            raise ValueError(
                f"Manufacturer mismatch: {device_manufacturer} != {user_manufacturer}"
            )

    # async def _check_mqtt_broker(self, mqtt_broker: str):
    #     mqtt_ip: str = mqtt_broker.split(":")[0]
    #     mqtt_port: int = int(mqtt_broker.split(":")[1]) if ":" in mqtt_broker else 1883
    #     try:
    #         await asyncio.wait_for(
    #             asyncio.open_connection(mqtt_ip, mqtt_port),
    #             timeout=2,
    #         )
    #     except (OSError, TimeoutError, asyncio.TimeoutError) as e:
    #         raise ValueError(
    #             f"MQTT broker {mqtt_broker}:{mqtt_port} is not reachable: {e}"
    #         ) from e
