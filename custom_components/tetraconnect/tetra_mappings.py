"""Contain all mapping methods and mapping data for TETRA message handling in tetraconnect integration."""


class Mappings:
    """Class to hold all mappings for TETRA data handling."""

    def acknowledgment_request_desc(self, acknowledgment_request: int) -> str:
        """Get the description for acknowledgment request."""
        acknowledgment_request_map = {
            0: "No acknowledgment requested",
            1: "Acknowledgment requested",
        }
        return acknowledgment_request_map.get(acknowledgment_request, "unknown")

    def application_identifier_description(
        self, application_identifier: int | None
    ) -> str:
        """Get the description for a given SDS type."""
        description_map = {
            9: "SDS Type 1",
            10: "SDS Type 2",
            11: "SDS Type 3",
            12: "SDS Transport Layer",
            13: "Status",
        }
        return description_map.get(application_identifier, "unknown")

    def application_identifier_type_length(
        self, application_identifier: int | None
    ) -> int:
        """Get the max length in bits for a given SDS type."""
        type_length_map = {
            9: 16,
            10: 32,
            11: 64,
            12: 2047,
            13: 16,
        }
        return type_length_map.get(application_identifier, 0)

    def confidence_level_desc(self, confidence_level_code: int) -> str:
        """Get confidence level based on binary data."""
        confidence_level_mapping = {
            0: "50%",
            1: "68%",
            2: "80%",
            3: "90%",
            4: "95%",
            5: "98%",
            6: "99%",
            7: "Confidence level not known",
        }
        return confidence_level_mapping.get(confidence_level_code, "unknown")

    def cme_error(self, error_code: int) -> str:
        """Get the error message for a given CME error code."""
        error_map = {
            3: "Operation not allowed",
            4: "Operation not supported",
            25: "Invalid characters in text string",
            33: "Parameter wrong type",
            34: "Parameter value out of range",
            35: "Syntax error",
            44: "Unknown parameter",
        }
        return error_map.get(error_code, "unknown")

    def direction_desc(self, direction_code: str) -> str:
        """Get travel direction value based on binary-data."""
        direction_mapping = {
            "0000": "N",
            "0001": "NNE",
            "0010": "NE",
            "0011": "ENE",
            "0100": "E",
            "0101": "ESE",
            "0110": "SE",
            "0111": "SSE",
            "1000": "S",
            "1001": "SSW",
            "1010": "SW",
            "1011": "WSW",
            "1100": "W",
            "1101": "WNW",
            "1110": "NW",
            "1111": "NNW",
        }
        return direction_mapping.get(direction_code, "unknown")

    def direction_of_travel_uncertainty_desc(self, uncertainty_code: int) -> str:
        """Get direction of travel uncertainty based on binary data."""
        direction_of_travel_uncertainty_mapping = {
            0: "< 1,5 °",
            1: "< 3 °",
            2: "< 6 °",
            3: "< 12 °",
            4: "< 24 °",
            5: "< 48 °",
            6: "< 96 °",
            7: "reserved",
        }
        return direction_of_travel_uncertainty_mapping.get(uncertainty_code, "unknown")

    def horizontal_velocity_uncertainty_desc(self, uncertainty_code: int) -> str:
        """Get horizontal velocity uncertainty based on binary data."""
        horizontal_velocity_uncertainty_mapping = {
            0: "< 1,5 km/h",
            1: "< 3 km/h",
            2: "< 6 km/h",
            3: "< 12 km/h",
            4: "< 24 km/h",
            5: "< 48 km/h",
            6: "< 96 km/h",
            7: "reserved",
        }
        return horizontal_velocity_uncertainty_mapping.get(uncertainty_code, "unknown")

    def identity_type(self, identity_type: int | None) -> str:
        """Get the description of the identity type."""
        type_mapping = {
            0: "ISSI",
            1: "GSSI",
            2: "SSI",
            3: "IP Address",
            4: "Telephone Number",
        }
        return type_mapping.get(identity_type, "other")

    def location_altitude_accuracy_desc(self, location_altitude_accuracy: int) -> str:
        """Get the description for a given location altitude accuracy."""
        location_altitude_accuracy_map = {
            0: "Less then 1 meter",
            1: "Less than 2 meters",
            2: "Less than 5 meters",
            3: "Less than 15 meters",
            4: "Less than 50 meters",
            5: "Less than 150 meters",
            6: "Less than 300 meters",
            7: "Best effort or not supported",
        }
        return location_altitude_accuracy_map.get(location_altitude_accuracy, "unknown")

    def location_altitude_calculation(self, location_altitude: int) -> float | None:
        """Calculate altitude from 12-bit encoded value.

        Args:
            K: 12-bit integer value (0-4095)

        Returns:
            Altitude in meters or None if reserved/invalid
        """
        if location_altitude == 0:
            return None  # Reserved
        elif 1 <= location_altitude <= 1201:
            # Range 1: -200m to 1000m in 1m steps
            return -200 + (location_altitude - 1) * 1
        elif 1202 <= location_altitude <= 1926:
            # Range 2: 1002m to 2450m in 2m steps
            return 1000 + (location_altitude - 1201) * 2
        elif 1927 <= location_altitude <= 2047:
            # Range 3: 2525m to 11525m in 75m steps
            return 2450 + (location_altitude - 1926) * 75
        else:
            # Values 2048-4095: undefined/reserved
            return None

    def location_altitude_type_desc(self, location_altitude_type: int) -> str:
        """Get the description for a given location altitude type."""
        location_altitude_type_map = {
            0: "Altitude above WGS84 ellipsoid",
            1: "User defined altitude reference",
        }
        return location_altitude_type_map.get(location_altitude_type, "unknown")

    def location_shape_desc(self, location_shape: int) -> str:
        """Get the description for a given location shape."""
        location_shape_map = {
            0: "No shape",
            1: "Location Point",
            2: "Location Circle",
            3: "Location Ellipse",
            4: "Location Point with Altitude",
            5: "Location Circle with Altitude",
            6: "Location Ellipse with Altitude",
            7: "Location Circle with Altitude and Altitude Uncertainty",
            8: "Location Ellipse with Altitude and Altitude Uncertainty",
            9: "Location Arc",
            10: "Location Point and Position Error",
            11: "Reserved",
            12: "Reserved",
            13: "Reserved",
            14: "Reserved",
            15: "Location Shape Extension, see note",
        }
        return location_shape_map.get(location_shape, "unknown")

    def motorola_status(self, status_code: str) -> str:
        """Get the Motorola device status based on the status code."""
        status_map = {
            "54000": "Power on, no network",
            "54001": "Scanning / searching for network",
            "54008": "Registered in network",
            "54009": "Registered in TMO, active",
            "54010": "DMO mode",
            "54020": "Network change / cell reselection",
        }
        return status_map.get(status_code, "unknown")

    def pdu_type_desc(self, pdu_type: int) -> str:
        """Get the description for a given PDU type."""
        pdu_type_map = {
            0: "Short location report",
            1: "Location protocol PDU with extension",
            2: "Reserved",
            3: "Reserved",
        }
        return pdu_type_map.get(pdu_type, "unknown")

    def pdu_type_ext_desc(self, pdu_type_ext: int) -> str:
        """Get the description for a given PDU type extension."""
        pdu_type_ext_map = {
            0b0000: "Reserved for further extension",
            0b0001: "Immediate location report request",
            0b0010: "Reserved",
            0b0011: "Long location report",
            0b0100: "Location report acknowledgement",
            0b0101: "Basic location parameters request/response",
            0b0110: "Add/modify trigger request/response",
            0b0111: "Remove trigger request/response",
            0b1000: "Report trigger request/response",
            0b1001: "Report basic location parameters request/response",
            0b1010: "Location reporting enable/disable request/response",
            0b1011: "Location reporting temporary control request/response",
            0b1100: "Backlog request/response",
            0b1101: "Reserved",
            0b1110: "Reserved",
            0b1111: "Reserved, see note",
        }
        return pdu_type_ext_map.get(pdu_type_ext, "unknown")

    def position_error_desc(self, error_code: str) -> str:
        """Get position error based on binary data."""
        position_error_mapping = {
            "000": "<2m",
            "001": "<20m",
            "010": "<200m",
            "011": "<2km",
            "100": "<20km",
            "101": "<=200km",
            "110": ">200km",
            "111": "error or unknown",
        }
        return position_error_mapping.get(error_code, "unknown")

    def reason_sending_desc(self, reason_sending: int) -> str:
        """Get the reason for sending based on the reason_sending value."""
        reason_for_sending_mapping = {
            0: "Subscriber unit is powered ON",
            1: "Subscriber unit is powered OFF",
            2: "Emergency condition is detected",
            3: "Push-to-talk condition is detected",
            4: "Status",
            5: "Transmit inhibit mode ON",
            6: "Transmit inhibit mode OFF",
            7: "System access (TMO ON)",
            8: "DMO ON",
            9: "Enter service (after being out of service)",
            10: "Service loss",
            11: "Cell reselection or change of serving cell",
            12: "Low battery",
            13: "Subscriber unit is connected to a car kit",
            14: "Subscriber unit is disconnected from a car kit",
            15: "Subscriber unit asks for transfer initialization configuration",
            16: "Arrival at destination",
            17: "Arrival at a defined location",
            18: "Approaching a defined location",
            19: "SDS type-1 entered",
            20: "User application initiated",
            21: "Lost ability to determine location",
            22: "Regained ability to determine location",
            23: "Leaving point",
            24: "Ambience Listening call is detected",
            25: "Start of temporary reporting",
            26: "Return to normal reporting",
            27: "Call setup type 1 detected",
            28: "Call setup type 2 detected",
            29: "Positioning device in MS ON",
            30: "Positioning device in MS OFF",
            32: "Response to an immediate location request",
            129: "Maximum reporting interval exceeded since the last location information report",
            130: "Maximum reporting distance limit travelled since last location information report",
        }
        return reason_for_sending_mapping.get(reason_sending, "unknown")

    def sds_command(self, sds_command: str) -> str:
        """Get the description of the SDS command."""
        command_mapping = {
            "+CTSDSR": "CT Short Data Service",
            "+GMM": "Model Identification",
            "+GMI": "Manufacturer Identification",
            "+GMR": "Revision Identification",
            "+CMEE": "Error Report",
            "+CME ERROR": "Error Report",
            "+ENCR": "Encryption Status",
        }
        return command_mapping.get(sds_command, "unknown")

    def sds_type(self, sds_type: int) -> str:
        """Get the description of the SDS type."""
        type_mapping = {
            10: "Short Location Report",
            128: "Status Report",
            130: "Long Location Report",
            131: "Position Request Reply",
            137: "Text Message",
            138: "Segmented Message",
        }
        return type_mapping.get(sds_type, "unknown")

    def type_add_data_desc(self, type_add_data) -> str:
        """Get the mapping for SDS type and additional data."""
        type_add_data_mapping = {
            0: "Reason for sending",
            1: "User defined data",
        }
        return type_add_data_mapping.get(type_add_data, "unknown")

    def time_elapsed_desc(self, time_elapsed) -> str:
        """Get the mapping for time elapsed."""
        time_elapsed_mapping = {
            0: "<5s",
            1: "<5min",
            2: "<30min",
            3: "Time elapsed not known or not applicable",
        }
        return time_elapsed_mapping.get(time_elapsed, "unknown")

    def time_type_desc(self, time_type: int) -> str:
        """Get the description for a given time type."""
        time_type_map = {
            0: "None",
            1: "Time elapsed",
            2: "Time of position",
            3: "Reserved",
        }
        return time_type_map.get(time_type, "unknown")

    def velocity_type_desc(self, velocity_type: int) -> str:
        """Get the description for a given velocity type."""
        velocity_type_map = {
            0: "No velocity information",
            1: "Horizontal velocity",
            2: "Horizontal velocity with uncertainty",
            3: "Horizontal velocity and vertical velocity",
            4: "Horizontal velocity and vertical velocity with uncertainty",
            5: "Horizontal velocity with direction of travel extended",
            6: "Horizontal velocity with direction of travel extended and uncertainty",
            7: "Horizontal velocity and vertical velocity with direction of travel extended and uncertainty",
        }
        return velocity_type_map.get(velocity_type, "unknown")

    def vertical_velocity_uncertainty_desc(
        self, vertical_velocity_uncertainty: int
    ) -> str:
        """Get vertical velocity uncertainty based on binary data."""
        vertical_velocity_uncertainty_mapping = {
            0: "< 1,5 km/h",
            1: "< 3 km/h",
            2: "< 6 km/h",
            3: "< 12 km/h",
            4: "< 24 km/h",
            5: "< 48 km/h",
            6: "< 96 km/h",
            7: "reserved",
        }
        return vertical_velocity_uncertainty_mapping.get(
            vertical_velocity_uncertainty, "unknown"
        )

    def vertical_velocity_calculation(self, vertical_velocity: int) -> float | str:
        """Calculate vertical velocity from 7-bit encoded value.

        Args:
            vertical_velocity: 7-bit integer value (0-127)

        Returns:
            Vertical velocity in km/h or descriptive string
        """
        if vertical_velocity <= 28:
            # Bereich 0-28: Linear 1 km/h steps
            return float(vertical_velocity)
        elif vertical_velocity <= 125:
            # Bereich 29-125: Exponentiell mit Basis 1.038 (3.8% steps)
            # Basis-Berechnung: bei K=29 sollte ~29.1 km/h rauskommen
            base_velocity = 29.1
            step_factor = 1.038
            return base_velocity * (step_factor ** (vertical_velocity - 29))
        elif vertical_velocity == 126:
            return "More than 1043 km/h"
        elif vertical_velocity == 127:
            return "Not known"
        else:
            return "unknown"

    def vertical_velocity_sign_desc(self, vertical_velocity_sign: int) -> str:
        """Get the description for a given vertical velocity sign."""
        vertical_velocity_sign_map = {
            0: "Velocity upward",
            1: "Velocity downward",
        }
        return vertical_velocity_sign_map.get(vertical_velocity_sign, "unknown")
