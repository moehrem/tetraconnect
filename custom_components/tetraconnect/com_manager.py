"""COM manager for tetraconnect integration."""

import asyncio
import contextlib
import logging

import serial
import serial_asyncio

from .const import (
    MAX_RETRY_ATTEMPTS,
    SLEEP_TIME_AFTER_FAILED_RECONNECT,
    SLEEP_TIME_CONNECTION_CHECK,
    SLEEP_TIME_RETRY,
    TETRA_DEFAULTS,
)
from .event_handler import fire_connection_changed
from .helpers import TetraconnectHelpers

_LOGGER = logging.getLogger(__name__)


class COMManager:
    """Manages serial COM connection lifecycle."""

    def __init__(self, coordinator, com_port: str, baudrate: int) -> None:
        """Initialize the COMManager."""
        self.coordinator = coordinator
        self.com_port = com_port
        self.baudrate = baudrate
        self.transport = None
        self.protocol = None
        self._tetra_defaults = TETRA_DEFAULTS.copy()
        self._connection_check_task = None
        self._failed_reconnect_count = 0  # Track consecutive failed reconnect attempts

        self.helpers = TetraconnectHelpers(coordinator)

    def set_connection_status(self, status: int, reason: str = "") -> None:
        """Centralized connection status update.

        Args:
            status: Status code (1=connected, 2=reconnecting, 3=disconnected)
            reason: Optional reason for the status change
        """
        status_mapping = {
            1: "connected",
            2: "reconnecting",
            3: "disconnected",
        }
        status_text = status_mapping.get(status, "unknown")
        if reason:
            _LOGGER.info("Connection status: %s (%s)", status_text, reason)
        else:
            _LOGGER.info("Connection status: %s", status_text)

        _LOGGER.debug("Calling helpers.update_connection_status(%d)", status)
        self.helpers.update_connection_status(status)
        _LOGGER.debug("Calling fire_connection_changed with status: %s", status_text)
        fire_connection_changed(self.coordinator.hass, status_text)

    async def serial_initialize(self, hass):
        """Start monitoring and connection loop."""
        self._connection_check_task = hass.loop.create_task(self._watchdog())

    async def serial_stop(self):
        """Stop connection and monitoring."""
        if self.transport:
            self.transport.close()
            self.transport = None
            self.protocol = None
        if self._connection_check_task:
            self._connection_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._connection_check_task

    async def _connect(self):
        """Try to establish the serial connection.

        This is handled in a loop of _periodic_connection_check, which also serves
        as watchdog for the serial connection.

        """

        self.set_connection_status(2, f"connecting to {self.com_port}")

        loop = asyncio.get_running_loop()
        (
            self.transport,
            self.protocol,
        ) = await serial_asyncio.create_serial_connection(
            loop,
            lambda: SerialHandler(self.coordinator),
            self.com_port,
            baudrate=self.baudrate,
        )
        self.set_connection_status(1, f"established on {self.com_port}")
        # await self._tetra_initialize()

    async def _watchdog(self):
        """Continuously ensure serial connection with exponential backoff.

        Permanently checking the serial connection every SLEEP_TIME_CONNECTION_CHECK seconds.
        If the connection is lost, it will try to reconnect with exponential backoff:
        - First MAX_RETRY_ATTEMPTS attempts with SLEEP_TIME_RETRY between retries
        - If all attempts fail, wait SLEEP_TIME_AFTER_FAILED_RECONNECT before trying again
        - Resets counter on successful connection

        """
        while True:
            if self.transport is None or self.transport.is_closing():
                self.set_connection_status(2, "detected, attempting to reconnect")

                attempt = 1
                while attempt <= MAX_RETRY_ATTEMPTS:
                    try:
                        await self._connect()
                        if self.transport and not self.transport.is_closing():
                            self.set_connection_status(1, "connected successfully")
                            self._failed_reconnect_count = 0  # Reset counter on success
                            await self.tetra_initialize()
                            break
                    except (
                        serial.SerialException,
                        OSError,
                        ValueError,
                        asyncio.CancelledError,
                    ) as e:
                        _LOGGER.warning(
                            "Connection attempt %d/%d failed: %s",
                            attempt,
                            MAX_RETRY_ATTEMPTS,
                            e,
                        )

                    attempt += 1

                    if attempt > MAX_RETRY_ATTEMPTS:
                        # ensure that serial connection is closed
                        if self.transport:
                            self.transport.close()
                            self.transport = None
                            self.protocol = None

                        # Increment failed reconnect counter for exponential backoff
                        self._failed_reconnect_count += 1

                        self.set_connection_status(
                            3,
                            f"reconnect failed after {MAX_RETRY_ATTEMPTS} attempts (backoff #{self._failed_reconnect_count})",
                        )
                        _LOGGER.error(
                            "Reconnect failed after %d attempts and %d seconds. "
                            "Entering exponential backoff (attempt #%d). "
                            "Please check the connection.",
                            MAX_RETRY_ATTEMPTS,
                            MAX_RETRY_ATTEMPTS * SLEEP_TIME_RETRY,
                            self._failed_reconnect_count,
                        )
                        break

                    await asyncio.sleep(SLEEP_TIME_RETRY)

                # After failed reconnect attempts, use exponential backoff
                if self._failed_reconnect_count > 0:
                    backoff_time = (
                        SLEEP_TIME_AFTER_FAILED_RECONNECT * self._failed_reconnect_count
                    )
                    _LOGGER.info(
                        "Waiting %d seconds before next reconnect attempt (backoff #%d)",
                        backoff_time,
                        self._failed_reconnect_count,
                    )
                    await asyncio.sleep(backoff_time)
                else:
                    # Normal monitoring interval
                    await asyncio.sleep(SLEEP_TIME_CONNECTION_CHECK)
            else:
                # Connection is active, reset backoff counter
                self._failed_reconnect_count = 0
                await asyncio.sleep(SLEEP_TIME_CONNECTION_CHECK)

    async def tetra_initialize(self):
        """Initialize TETRA device for specific CTSP-Services.

        Initialize the device for TETRA services by sending standard AT commands.
        Wait for the answer on each command and log an error if the command fails.
        This will not create any entities, its just for device initialization.

        Device information like model, sw-version, revision, manufacturer were
        already requested in the config flow, so we do not request them again here.

        """
        # these commands are standard TETRA commands, which every device should respond to

        _LOGGER.info(
            "##### Start initializing TETRA services on %s #####", self.com_port
        )

        if not self.transport or not self.protocol:
            for _ in range(5):
                await asyncio.sleep(0.2)
                if self.transport and self.protocol:
                    break
            else:
                _LOGGER.warning(
                    "No serial connection available, initializing TETRA device failed"
                )
                return

        init_raw_data = {}

        # +CTSP=<service profile>, <service layer1>, [<service layer2>], [<AI mode>], [<link identifier>]
        service_commands = [
            # "AT+CTSP=1,2,20\r\n",  # Status TE
            "AT+CTSP=2,2,20\r\n",  # Status MT & TE
            "AT+CTSP=1,3,130\r\n",  # Textnachrichten einschalten
            "AT+CTSP=1,3,131\r\n",  # GPS einschalten
            "AT+CTSP=1,3,10\r\n",  # Status GPS
            "AT+CTSP=1,3,137\r\n",  # Immediate Text
            "AT+CTSP=1,3,138\r\n",  # Alarm
            # "AT+CTSP=2,0\r\n",
            # "AT+CTSP=2,1\r\n",
            # "AT+CTSP=2,2\r\n",
            # "AT+CTSP=2,3\r\n",
            # "AT+CTSP=2,4\r\n",
        ]

        # send commands and wait for responses
        # a live connection does not mean a valid response on TETRA commands
        # so we have to handle timeout errors and als ConfigEntryNotReady here
        try:
            self.protocol.expect_response = True
            self.protocol.response_future = asyncio.get_running_loop().create_future()
            for cmd in service_commands:
                _LOGGER.debug("Sending service profile command: %s", cmd.strip())
                self.transport.write(cmd.encode())
                await asyncio.sleep(0.1)

                try:
                    response = await asyncio.wait_for(
                        self.protocol.response_future, timeout=5
                    )
                    self.protocol.expect_response = False
                    init_raw_data[cmd] = response
                    _LOGGER.debug(
                        "Received response for command %s: %s", cmd.strip(), response
                    )
                except TimeoutError:
                    _LOGGER.error(
                        "Timeout while waiting for response to command: %s", cmd.strip()
                    )
                    init_raw_data[cmd] = b"CME ERROR: response timeout"
                    continue
        except asyncio.CancelledError:
            _LOGGER.warning("Tetra initialization was cancelled by Home Assistant")
            raise asyncio.CancelledError from None

        # check responses
        for cmd, resp in init_raw_data.items():
            if resp != b"\r\nOK\r\n":
                _LOGGER.warning(
                    "Service profile command '%s' failed with response: %s",
                    cmd.strip().replace("\r\n", ""),
                    resp.decode("utf-8").strip().replace("\r\n", ""),
                )

        _LOGGER.info(
            "##### Finished initializing TETRA services on %s #####", self.com_port
        )


class SerialHandler(asyncio.Protocol):
    """Handles serial connection incl incoming data."""

    def __init__(self, coordinator) -> None:
        """Initialize the data handler."""
        self.coordinator = coordinator
        self.raw_data = b""
        self.decoded_data = None
        self.remaining = b""

        self.helpers = TetraconnectHelpers(coordinator)
        self.expect_response = False
        self.response_future = None

    def connection_made(self, transport):
        """Handle the connection being made."""
        self.transport = transport
        _LOGGER.debug("Serial connection opened")

    def data_received(self, data):
        """Handle incoming data."""

        _LOGGER.debug("Raw data received: %s", data)

        # check if expected response is set -> wait for response
        if self.expect_response:
            # Set result only if not already done
            if self.response_future is not None and not self.response_future.done():
                self.response_future.set_result(data)

        else:
            self.coordinator.handle_serial_data(data)

    def connection_lost(self, exc):
        """Handle the connection being lost."""
        self.coordinator.com_manager.set_connection_status(3, f"lost: {exc}")
