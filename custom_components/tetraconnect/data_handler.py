"""General data handling for tetraconnect integration."""

import logging
import math

from .const import SDS_TYPE_USER_DATA_WHITELIST, MAX_BUFFER_BYTES
from .event_handler import fire_error, fire_message_received
from .tetra_mappings import Mappings

_LOGGER = logging.getLogger(__name__)


class TetraConnectDataHandler:
    """Handles data processing for tetraconnect integration."""

    def __init__(self, coordinator) -> None:
        """Initialize DataHandler."""
        self.coordinator = coordinator
        self.wb = coordinator.working_buffer
        self.pb = coordinator.persistent_buffer

        self.handler_module = coordinator.handler_module
        self.mappings = Mappings()

    def data_handler(self) -> None:
        """Process incoming data through all handling steps.

        1. raw bytes (persistent_buffer)
                ↓
        2. SDSFrameAssembler
                ↓
        3. complete SDS-Frames (bytes)
                ↓
        4. SDSParser and Decoder
                ↓
        5. Manufacturer specific message handling
                ↓
        6. Events


        """

        # extract complete frames from persistent buffer
        frames = self._extract_complete_frames()
        if not frames:
            return

        # process each complete frame
        for frame in frames:
            frame_data = {}
            frame_data["error"] = {}
            message = {}
            frame_data["raw_frame"] = frame

            try:
                self._parse_decode_frame(frame_data)

                # if frame not OK, continue with next frame
                if not self._validate_frame(frame_data):
                    continue

                self._apply_manufacturer_logic(frame_data, message)
                self._fire_events(frame_data, message)
            except (ValueError, KeyError):
                for key, error in frame_data["error"].items():
                    _LOGGER.error("Frame processing error - %s: %s", key, error)
                self._fire_events(frame_data, message)
                continue

    def _extract_complete_frames(self) -> list[bytes]:
        r"""Extract complete SDS frames from the persistent buffer.

        Each frame consists of a header (\r\n+...\r\n) and optional user data (not starting with +, ending with \r\n).
        """
        frames = []
        buffer = self.pb.raw_data

        # buffer size check and trim if necessary to prevent memory issues with malformed data
        if len(buffer) > MAX_BUFFER_BYTES:
            removed_length = len(buffer) - MAX_BUFFER_BYTES
            _LOGGER.warning(
                "Persistent buffer exceeded %s bytes, trimming oldest data (%s bytes removed)",
                MAX_BUFFER_BYTES,
                removed_length,
            )

            buffer = buffer[-MAX_BUFFER_BYTES:]
            self.pb.raw_data = buffer

        # check if there is at least one complete line
        if b"\r\n" not in buffer:
            return frames

        whitelist = {item.encode("utf-8") for item in SDS_TYPE_USER_DATA_WHITELIST}

        def _message_type(header_line: bytes) -> bytes | None:
            plus_pos = header_line.find(b"+")
            if plus_pos == -1:
                return None

            semicolon_pos = header_line.find(b";", plus_pos + 1)
            colon_pos = header_line.find(b":", plus_pos + 1)
            delimiter_pos = semicolon_pos if semicolon_pos != -1 else colon_pos
            if delimiter_pos == -1:
                return None

            return header_line[plus_pos:delimiter_pos]

        def _requires_user_data(header_line: bytes) -> bool:
            message_type = _message_type(header_line)
            if message_type is None:
                return False
            return message_type in whitelist

        parts = buffer.split(b"\r\n")
        if buffer.endswith(b"\r\n"):
            lines = parts[:-1]
            remainder = b""
        else:
            lines = parts[:-1]
            remainder = parts[-1]

        pending_header: bytes | None = None
        pending_requires_user_data = False

        for line in lines:
            if not line:
                continue

            if pending_header is None:
                if not line.startswith(b"+"):
                    continue

                pending_header = line
                pending_requires_user_data = _requires_user_data(line)
                if pending_requires_user_data:
                    continue

                frames.append(pending_header + b"\r\n")
                pending_header = None
                continue

            frames.append(pending_header + b"\r\n" + line + b"\r\n")
            pending_header = None

        if pending_header is not None:
            if pending_requires_user_data:
                remainder = pending_header + b"\r\n" + remainder
            else:
                frames.append(pending_header + b"\r\n")

        self.pb.raw_data = remainder
        return frames

    def _parse_decode_frame(self, frame_data: dict) -> None:
        """Parse a complete SDS frame into its components.

        Parse frames into header and user_data based on SDS frame structure.

        """

        # extract header fields
        header_start = frame_data["raw_frame"].find(b"+")
        header_end = frame_data["raw_frame"].index(b"\r\n", header_start)
        header_byte = frame_data["raw_frame"][header_start:header_end]
        header = header_byte.decode("utf-8", errors="ignore").strip()

        # extract user data which is not available for all message types
        try:
            user_data_start = header_end + 2  # skip \r\n
            user_data_byte = frame_data["raw_frame"][user_data_start:]
            user_data = user_data_byte.decode("utf-8", errors="ignore").strip()
        except ValueError:
            user_data = ""

        # set parsed data
        frame_data["header"] = header
        frame_data["user_data"] = user_data

    def _validate_frame(self, frame_data: dict) -> bool:
        """Validate the parsed SDS frame data.

        Validate the frame by checking if the user data length matches the expected length from the header for message types with user data.
        Using whitelist constant SDS_TYPE_WHITELIST for message types with expected user data.

        """

        header = frame_data["header"]
        user_data = frame_data["user_data"]

        # extract message type from header
        message_type = header.split(":", 1)[0].strip()

        if message_type in SDS_TYPE_USER_DATA_WHITELIST:
            # if expect user data but none present
            if not user_data:
                _LOGGER.debug("No user data present but expected for header %s", header)
                self.pb.raw_data = frame_data["raw_frame"] + self.pb.raw_data
                return False

            # extract expected length in bits from header
            payload = header.split(":", 1)[1].strip()
            fields = [f.strip() for f in payload.split(",")]

            length_bits = None
            for field in reversed(fields):
                if field.isdigit():
                    length_bits = int(field)
                    break

            if length_bits is None:
                frame_data["error"]["No length field"] = (
                    "Length field expected, but could not find it."
                )
                raise ValueError

            # calculate expected length in bytes
            expected_length_bytes = math.ceil(length_bits / 8)

            # validate user data length
            actual_length_bytes = len(user_data) // 2  # hex string to bytes
            if actual_length_bytes != expected_length_bytes:
                frame_data["error"]["Length mismatch"] = (
                    f"User data length mismatch: expected {expected_length_bytes} bytes, got {actual_length_bytes} bytes"
                )
                raise ValueError

            # check ai_service and lenghth consistency
            ai_service = fields[0]
            if ai_service.isdigit():
                ai_service = int(ai_service)
                ai_service_max_length = (
                    self.mappings.application_identifier_type_length(ai_service)
                )

                if ai_service_max_length is not None:
                    if not length_bits <= ai_service_max_length:
                        ai_service_desc = (
                            self.mappings.application_identifier_description(ai_service)
                        )
                        frame_data["error"]["AI service length mismatch"] = (
                            f"AI service '{ai_service_desc}' expects maximum length of {ai_service_max_length} bits, got {length_bits} bits"
                        )
                        raise ValueError

        return True

    def _apply_manufacturer_logic(self, frame_data: dict, message: dict) -> None:
        """Apply manufacturer-specific logic to decoded frame data."""
        if not self.handler_module or not hasattr(self.handler_module, "process_data"):
            _LOGGER.error(
                "Manufacturer handler module does not have a process_data method"
            )
            return

        try:
            self.handler_module.process_data(frame_data, message)
        except Exception as e:
            frame_data["error"]["Manufacturer processing error"] = (
                f"Error in manufacturer-specific processing: {e}"
            )
            raise ValueError from e

    def _fire_events(self, frame_data: dict, message: dict) -> None:
        """Fire events for complete and invalid messages."""

        # event if error in frame data
        if frame_data.get("error"):
            _LOGGER.debug("##### Start firing events for errors #####")
            try:
                fire_error(
                    self.coordinator.hass,
                    {
                        "errors": frame_data["error"],
                        "raw_frame": frame_data["raw_frame"].decode(
                            "utf-8", errors="ignore"
                        ),
                    },
                )
            except (ValueError, KeyError, TypeError) as err:
                fire_error(
                    self.coordinator.hass, {"error": f"Failed to process event: {err}"}
                )
                _LOGGER.error(
                    "Error firing event for invalid frame data: %s",
                    err,
                )
            _LOGGER.debug("##### End firing events for errors #####")
            return

        # event for message
        if message:
            _LOGGER.debug("##### Start firing events for messages #####")
            try:
                fire_message_received(self.coordinator.hass, message)
            except (ValueError, KeyError, TypeError) as err:
                fire_error(
                    self.coordinator.hass, {"error": f"Failed to process event: {err}"}
                )
                _LOGGER.error("Error firing event for message: %s", err)
            _LOGGER.debug("##### End firing events for messages #####")
