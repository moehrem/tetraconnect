"""Constants for the tetraconnect integration."""

import json
from pathlib import Path

# version info from manifest.json
_MANIFEST_PATH = Path(__file__).parent / "manifest.json"
with _MANIFEST_PATH.open(encoding="utf-8") as manifest_file:
    _MANIFEST = json.load(manifest_file)

_VERSION_PARTS: list[str] = _MANIFEST["version"].split(".")
VERSION = int(_VERSION_PARTS[0])
MINOR_VERSION = int(_VERSION_PARTS[1])
PATCH_VERSION = int(_VERSION_PARTS[2])


# general
DOMAIN = "tetraconnect"
MANUFACTURERS_LIST = ["Motorola"]
MAX_BUFFER_BYTES = 65536  # Maximum buffer size for reading from the serial port
SLEEP_TIME_CONNECTION_CHECK = 10  # Sleep time in seconds between connection checks
MAX_RETRY_ATTEMPTS = 5  # Maximum number of attempts to connect to the device
SLEEP_TIME_RETRY = 5  # Sleep time in seconds between retries
SLEEP_TIME_AFTER_FAILED_RECONNECT = (
    300  # Sleep time in seconds after failed reconnect attempts (5 minutes)
)
BAUDRATE = 38400
TETRA_DEFAULTS: dict[str, object] = {
    # general
    "tetra_command": "",
    "tetra_command_desc": "",
    "tetra_content": "",
}
LOG_FILE = "home-assistant.log"
LINE_COMMANDS: dict[str, str] = {
    "+CTSDSR": "multi",
    "+GMM": "single",
    "+GMR": "single",
    "+GMI": "single",
    "+CMEE": "single",
    "+CME ERROR": "single",
}

SDS_TYPE_USER_DATA_WHITELIST: list[str] = [
    "+CTSDSR",
    # Add other message types with user data here
]

# events
EVENT_MESSAGE_RECEIVED = "tetraconnect_message_received"
EVENT_ERROR = "tetraconnect_error"
EVENT_CONNECTION_CHANGED = "tetraconnect_connection_changed"


# Motorola specific
MOTOROLA_VARIABLES_DEFAULTS: dict[str, object] = {
    # general
    "sds_command": "unknown",
    "sds_command_desc": "unknown",
    "sds_content": "unknown",
    "validity": "valid",
    "invalid_message": "unknown",
    # +CTSDSR
    "sds_type": 0,
    "sds_type_desc": "unknown",
    "sds_lenght_bits": 0,
    "ai_service": 0,
    "issi_sen": 0,
    "issi_sen_type": 0,
    "issi_rec": 0,
    "issi_rec_type": 0,
    "lat": 0.0,
    "lng": 0.0,
    "velocity": 0,
    "direction": "unknown",
    "position_error": "unknown",
    "tetra_status": 0,
    "time_elapsed": "unknown",
    "pdu_type": 0,
    "type_additional_data_desc": "unknown",
    "reason_sending_desc": "unknown",
    "user_defined_data": 0,
    # +GMM
    "device_status": "unknown",
    "device_id": "unknown",
    "sw_version": 0,
    # +GMR
    "revision": "unknown",
    # +GMI
    "manufacturer": "unknown",
    # +CMEE & +CME ERROR & +CMEERROR
    "cme_error_code": 0,
    "cme_error_message": "unknown",
}

MOTOROLA_VARIABLES_CTSDSR_10: dict[str, object] = {
    # general
    "sds_command": "unknown",
    "sds_command_desc": "unknown",
    # "sds_content": "unknown",
    "validity": "valid",
    # +CTSDSR 10
    "sds_type": 0,
    "sds_type_desc": "unknown",
    "sds_lenght_bits": 0,
    "ai_service": 0,
    "issi_sen": 0,
    "issi_sen_type": 0,
    "issi_rec": 0,
    "issi_rec_type": 0,
    "lat": 0.0,
    "lng": 0.0,
    "velocity": 0,
    "direction": "unknown",
    "position_error": "unknown",
    "time_elapsed": "unknown",
    "pdu_type": 0,
    "type_additional_data_desc": "unknown",
    "reason_sending_desc": "unknown",
    "user_defined_data": 0,
}

MOTOROLA_VARIABLES_CTSDSR_128: dict[str, object] = {
    # general
    "sds_command": "unknown",
    "sds_command_desc": "unknown",
    # "sds_content": "unknown",
    "validity": "valid",
    # +CTSDSR 128
    "sds_type": 0,
    "sds_type_desc": "unknown",
    "sds_lenght_bits": 0,
    "ai_service": 0,
    "issi_sen": 0,
    "issi_sen_type": 0,
    "issi_rec": 0,
    "issi_rec_type": 0,
    "tetra_status": 0,
}

MOTOROLA_VARIABLES_GMM: dict[str, object] = {
    # general
    "sds_command": "unknown",
    "sds_command_desc": "unknown",
    # "sds_content": "unknown",
    "validity": "valid",
    # +GMM
    "device_status": "unknown",
    "device_id": "unknown",
    "sw_version": 0,
}

MOTOROLA_VARIABLES_GMR: dict[str, object] = {
    # general
    "sds_command": "unknown",
    "sds_command_desc": "unknown",
    # "sds_content": "unknown",
    "validity": "valid",
    # +GMR
    "revision": "unknown",
}

MOTOROLA_VARIABLES_GMI: dict[str, object] = {
    # general
    "sds_command": "unknown",
    "sds_command_desc": "unknown",
    # "sds_content": "unknown",
    "validity": "valid",
    # +GMI
    "manufacturer": "unknown",
}

MOTOROLA_VARIABLES_CMEE: dict[str, object] = {
    # general
    "sds_command": "unknown",
    "sds_command_desc": "unknown",
    # "sds_content": "unknown",
    "validity": "valid",
    # +CMEE & +CME ERROR
    "cme_error_code": 0,
    "cme_error_message": "unknown",
}

MOTOROLA_VARIABLES_GMM: dict[str, object] = {
    # general
    "sds_command": "unknown",
    "sds_command_desc": "unknown",
    # "sds_content": "unknown",
    "validity": "valid",
    # +CMEE & +CME ERROR & +CMEERROR
    "cme_error_code": 0,
    "cme_error_message": "unknown",
}

MOTOROLA_VARIABLES_UNKNOWN: dict[str, object] = {
    # general
    "sds_command": "unknown",
    "sds_command_desc": "unknown",
    "sds_content": "unknown",
    "validity": "valid",
}
