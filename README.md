# tetraconnect Home Assistant Integration

The **tetraconnect** integration allows you to connect and monitor TETRA radios (e.g., Motorola devices) via serial interface in [Home Assistant](https://www.home-assistant.io/). It provides real-time data by decoding decrypted TETRA messages into readable information and releasing them as events.

> ⚠️ **Important:** This integration cannot decode encrypted TETRA messages. You need legal access to decrypted data via a suitable hardware device.

> 🚧 **Early Stage Development:** This integration is not yet feature-complete, fully polished, or extensively tested. Please be aware of potential bugs and report any issues on [GitHub](https://github.com/moehrem/tetraconnect/issues).

## Features

- Automatic detection and configuration of supported TETRA radios
- Decoding of supported message types
- Event based message publishing
- mainly based on ETSI EN 300 392‑5 V2.7.1 (April 2020)

## Supported Manufacturers

According to the ETSI standard, each manufacturer can define custom data structures within specific limits. Therefore, data handling is manufacturer-specific.

**Currently Supported:**

- Motorola

**Planned Support:**

- Sepura

If you have information about other manufacturers or can provide documentation, please [contact us](https://github.com/moehrem/tetraconnect/issues). Thank you!

## Installation

### HACS (Recommended)

tetraconnect is not yet available via HACS but can be installed manually:

1. [Install HACS](https://www.hacs.xyz/docs/use/) if not already done
2. [![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=moehrem&repository=tetraconnect&category=Integration)
3. Click "Download" in the bottom-right corner

### Manual Installation

1. Copy the `custom_components/tetraconnect` directory into your Home Assistant `custom_components` folder
2. Restart Home Assistant

## Configuration

### Via Home Assistant UI

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for **tetraconnect** and follow the setup wizard:
   - Select your device manufacturer
   - Choose the serial port and baudrate
   - The integration will auto-detect your device and complete the setup

### Configuration Options

| Option           | Description                                      | Default  |
| ---------------- | ------------------------------------------------ | -------- |
| **Manufacturer** | Supported manufacturer (e.g., Motorola)          | Required |
| **Serial Port**  | Path to the serial device (e.g., `/dev/ttyUSB0`) | Required |
| **Baudrate**     | Communication speed                              | 38400    |

## Sensors

The integration creates a single **Connection Status** sensor for diagnostic purposes.

## Events

The integration publishes incoming TETRA messages as Home Assistant events. There are three event types:

| Event Type                        | Description                    |
| --------------------------------- | ------------------------------ |
| `tetraconnect_message_received`   | Incoming TETRA message         |
| `tetraconnect_error`              | Connection or processing error |
| `tetraconnect_connection_changed` | Connection status change       |

**Test:** Listen to events in **Developer Tools** → **Events**. Enter one of the event types above to monitor incoming messages. See [Home Assistant Events Documentation](https://www.home-assistant.io/integrations/event/) for more details.

**Usage:** You may use events as triggers for automations or create your own entities from it.

## Messages

Incoming messages have different types per TETRA standard. Each type contains different data fields. Below are the Motorola message types that are currently parsed into structured fields.

> ℹ️ **Note:** Only the message types listed below are parsed into structured fields. **All** incoming messages are published as events. Unsupported message or SDS types result in a `tetraconnect_error` event with the raw frame and error details.

### +CTSDSR (SDS)

Common header fields for all +CTSDSR messages:

| Field                              | Description                        |
| ---------------------------------- | ---------------------------------- |
| `message_type`                     | Message type ("+CTSDSR")           |
| `air_interface_service`            | Air interface service identifier   |
| `air_interface_service_desc`       | Air interface service description  |
| `calling_party_identity`           | Sender identity                    |
| `calling_party_identity_type`      | Sender identity type               |
| `calling_party_identity_type_desc` | Sender identity type description   |
| `called_party_identity`            | Receiver identity                  |
| `called_party_identity_type`       | Receiver identity type             |
| `called_party_identity_type_desc`  | Receiver identity type description |
| `length_bits`                      | Total user data length in bits     |
| `end_to_end_encryption`            | End-to-end encryption indicator    |
| `sds_type`                         | SDS type (for example, 10 or 128)  |
| `sds_type_desc`                    | SDS type description               |

#### SDS type 10, length 88 (Short Location Report)

| Field               | Description                      |
| ------------------- | -------------------------------- |
| `pdu_type`          | PDU type description             |
| `time_elapsed`      | Time elapsed description         |
| `position_error`    | Position accuracy description    |
| `direction`         | Direction of travel description  |
| `reason_sending`    | Reason for sending description   |
| `type_add_data`     | Additional data type description |
| `user_defined_data` | User defined data                |
| `lng`               | Longitude                        |
| `lat`               | Latitude                         |
| `velocity`          | Velocity (number or "unknown")   |

#### SDS type 10, length 168 (Extended Short Location Report)

Depending on location shape and velocity type, some of these fields are present:

| Field                                      | Description                                  |
| ------------------------------------------ | -------------------------------------------- |
| `pdu_type`                                 | PDU type description                         |
| `pdu_type_extension`                       | PDU type extension description               |
| `time_elapsed`                             | Time elapsed description                     |
| `time_of_position`                         | Time of position (day, hour, minute, second) |
| `longitude`                                | Longitude                                    |
| `latitude`                                 | Latitude                                     |
| `horizontal_position_uncertainty`          | Horizontal position uncertainty              |
| `half_of_major_axis`                       | Half of major axis                           |
| `half_of_minor_axis`                       | Half of minor axis                           |
| `angle`                                    | Ellipse angle                                |
| `confidence_level`                         | Confidence level description                 |
| `location_altitude_type`                   | Location altitude type description           |
| `location_altitude`                        | Location altitude                            |
| `altitude_uncertainty`                     | Altitude uncertainty                         |
| `location_altitude_accuracy`               | Location altitude accuracy description       |
| `inner_radius`                             | Inner radius (meters)                        |
| `outer_radius`                             | Outer radius (meters)                        |
| `start_angle`                              | Start angle                                  |
| `stop_angle`                               | Stop angle                                   |
| `position_error`                           | Position accuracy description                |
| `location_shape_extension`                 | Location shape extension                     |
| `horizontal_velocity`                      | Horizontal velocity                          |
| `horizontal_velocity_uncertainty`          | Horizontal velocity uncertainty description  |
| `vertical_velocity_sign`                   | Vertical velocity sign description           |
| `vertical_velocity`                        | Vertical velocity                            |
| `vertical_velocity_uncertainty`            | Vertical velocity uncertainty description    |
| `direction_of_travel_extended`             | Direction of travel (extended)               |
| `direction_of_travel_extended_uncertainty` | Direction of travel uncertainty description  |
| `acknowledgment_request`                   | Acknowledgment request description           |
| `type_add_data`                            | Additional data type description             |
| `reason_sending`                           | Reason for sending description               |
| `motorola_extension_blob`                  | Motorola specific extension (hex string)     |

#### SDS type 128 (Status Report)

| Field         | Description           |
| ------------- | --------------------- |
| `status_code` | Status code (numeric) |

### +ENCR (Encryption status)

| Field          | Description                        |
| -------------- | ---------------------------------- |
| `message_type` | Message type ("+ENCR")             |
| `ai_service`   | Air interface service identifier   |
| `opta`         | Manufacturer specific option field |

### Other message types

Unsupported message types or SDS types are published as `tetraconnect_error` events with the raw frame and error details. If you need support for a specific message type, please [create an issue](https://github.com/moehrem/tetraconnect/issues).

## Troubleshooting

### Diagnostics

The integration provides downloadable diagnostics per device, including logs and event data.

> ℹ️ **Note:** Event logging is not persistent and will reset after Home Assistant restarts. Thats not an intergation issue, but works as intended by HA.

### Troubleshooting Tips

Error logs should be self explanatory, but if you still need more details, set log level to debug.
If you're not sure about an error just create an issue and we'll check on that together!
