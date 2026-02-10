"""Handle communication with Motorola devices."""

import logging
from typing import Any

from .const import (
    MOTOROLA_VARIABLES_DEFAULTS,
    MOTOROLA_VARIABLES_CTSDSR_10,
    MOTOROLA_VARIABLES_CTSDSR_128,
    MOTOROLA_VARIABLES_GMM,
    MOTOROLA_VARIABLES_CMEE,
    MOTOROLA_VARIABLES_GMI,
    MOTOROLA_VARIABLES_GMR,
    MOTOROLA_VARIABLES_UNKNOWN,
)

from .tetra_mappings import Mappings

_LOGGER = logging.getLogger(__name__)


class Motorola:
    """Handle Motorola specific message processing."""

    def __init__(self, coordinator) -> None:
        """Initialize Motorola handler."""
        self.coordinator = coordinator
        self.mappings = Mappings()

        self.frame_data = {}
        self.message = {}
        self.working_header = None
        self.working_user_data = None

        self.supported_message_types = [
            "+CTSDSR",
            "+GMM",
            "+CMEE",
            "+CME ERROR",
            "+CMEERROR",
            "+GMI",
            "+GMR",
            "+ENCR",
        ]

        self.supported_sds_types = [10, 128]

    def process_data(self, frame_data: dict[str, Any], message: dict[str, Any]) -> None:
        """Process Motorola specific message.

        This method is expected to exist in any manufacturer-specific handler class. It will be called from the general data handler after parsing and decoding the SDS frame.
        The name of the file must be the lowercase manufacturer name, the class name the capitalized manufacturer name. I.e. "motorola.py" with class "Motorola".

        You must populate the dict "message" with the processed data fields. This dict will late be used to fire events with the processed data.

        With any error you may raise ValueError or KeyError with an appropriate error message in frame_data["error"]. This will be caught in the data_handler.
        Error messages must specify the manufacturer in your message to help identifying the source of the error.

        Args:
            frame_data (dict[str, Any]): Parsed frame data including user_data.
                frame_data["header"]: header information as bytes
                frame_data["user_data"]: user data as bytes
            message (dict[str, Any]): Message dictionary to populate with processed data.

        Returns:
            message (dict): Updated frame data with Motorola specific fields.

        """

        self.frame_data = frame_data
        self.message = message
        self.working_header = []
        self.working_user_data = []

        # parse data
        self._parse_frame_data(frame_data)

        # check working header exists
        if not self.working_header:
            frame_data["error"]["Missing header"] = (
                "Header is missing or could not be parsed. Please create an issue at https://github.com/moehrem/tetraconnect/issues"
            )
            raise ValueError

        # validate message type
        if self.message["message_type"] not in self.supported_message_types:
            frame_data["error"]["Unsupported message type"] = (
                f"'{self.message['message_type']}' not supported. Please create an issue at https://github.com/moehrem/tetraconnect/issues"
            )
            raise ValueError

        # process message type
        match self.message["message_type"]:
            # handling of messages by type
            # add more message types as needed
            case "+CTSDSR":
                self._process_ctsdsr(frame_data, message)

            case "+ENCR":
                self._process_encr(frame_data, message)

            case _:
                frame_data["error"]["Unsupported message type"] = (
                    f"'{self.message['message_type']}' not supported. Please create an issue at https://github.com/moehrem/tetraconnect/issues"
                )
                raise ValueError

    def _parse_frame_data(self, frame_data: dict) -> None:
        """Parse Motorola specific frame data.

        Clear and split header and user data as needed.
        Expect first entry of working_header to be message type.

        Args:
            frame_data (dict): Parsed frame data including user_data.

        Returns:
            dict: Updated frame data with Motorola specific fields.

        """

        # parse header
        header = frame_data["header"]
        header = header.replace(" ", "")
        header = header.replace("\r\n", "")
        header = header.replace(":", ",").strip()
        header_list = header.split(",")
        self.working_header = header_list

        message_type = self.working_header[0]
        self.message["message_type"] = message_type

        # parse user data
        user_data = frame_data["user_data"]
        user_data = user_data.replace("\r\n", "")
        user_data = user_data.strip()
        self.working_user_data = user_data

    def _process_ctsdsr(
        self, frame_data: dict[str, Any], message: dict[str, Any]
    ) -> None:
        """Process +CTSDSR message type.

        Args:
            frame_data (dict[str, Any]): Parsed frame data including user_data.
            message (dict[str, Any]): Message dictionary to populate with processed data.

        Returns:
            dict[str, Any]: Updated frame data with +CTSDSR specific fields.

        """

        # header fields
        message["air_interface_service"] = (
            int(self.working_header[1])
            if len(self.working_header) > 1 and self.working_header[1].isdigit()
            else None
        )
        message["air_interface_service_desc"] = (
            self.mappings.application_identifier_description(
                message["air_interface_service"]
            )
        )
        message["calling_party_identity"] = (
            int(self.working_header[2])
            if len(self.working_header) > 2 and self.working_header[2].isdigit()
            else None
        )
        message["calling_party_identity_type"] = (
            int(self.working_header[3])
            if len(self.working_header) > 3 and self.working_header[3].isdigit()
            else None
        )
        message["calling_party_identity_type_desc"] = self.mappings.identity_type(
            message["calling_party_identity_type"]
        )
        message["called_party_identity"] = (
            int(self.working_header[4])
            if len(self.working_header) > 4 and self.working_header[4].isdigit()
            else None
        )
        message["called_party_identity_type"] = (
            int(self.working_header[5])
            if len(self.working_header) > 5 and self.working_header[5].isdigit()
            else None
        )
        message["called_party_identity_type_desc"] = self.mappings.identity_type(
            message["called_party_identity_type"]
        )
        message["length_bits"] = (
            int(self.working_header[6])
            if len(self.working_header) > 6 and self.working_header[6].isdigit()
            else None
        )
        message["end_to_end_encryption"] = (
            self.working_header[7] if len(self.working_header) > 7 else None
        )

        # message["message_type"] = frame_data.get("header", {}).get("message_type", "")

        ## user data fields
        message["sds_type"] = (
            int(self.working_user_data[0:2], 16)
            if len(self.working_user_data) >= 2
            else None
        )

        # map type to description
        message["sds_type_desc"] = self.mappings.sds_type(message["sds_type"])

        # start user data processing based on sds type
        match message["sds_type"]:
            # Short Location Report
            # Motorolla uses sds-type '10' for Short Location Report with 88 bytes
            # but also sends 'long location report' also as sds-type '10' with 168 bytes incl vendor specific data
            case 10:
                if message["length_bits"] == 88:
                    self._self_process_short_location_report_88(frame_data, message)
                elif message["length_bits"] == 168:
                    self._self_process_short_location_report_168(frame_data, message)
                else:
                    _LOGGER.warning(
                        "Unsupported length for Short Location Report for Motorola: %s",
                        message["length_bits"],
                    )
                    frame_data["error"]["Unsupported Short Location Report length"] = (
                        f"Length '{message['length_bits']}' not supported. Please create an issue at https://github.com/moehrem/tetraconnect/issues"
                    )

            # status report
            case 128:
                self._self_process_status_report(frame_data, message)

            # long location report
            case 130:
                # TODO implement processing of long location report
                _LOGGER.warning(
                    "Long location report processing not implemented yet. Please create an issue at https://github.com/moehrem/tetraconnect/issues"
                )

            # position request reply
            case 131:
                # TODO implement processing of position request reply
                _LOGGER.warning(
                    "Position request reply processing not implemented yet. Please create an issue at https://github.com/moehrem/tetraconnect/issues"
                )

            # unsupported sds type
            case _:
                _LOGGER.warning(
                    "Unsupported SDS type for Motorola: %s", message["sds_type"]
                )
                frame_data["error"]["Unsupported SDS type"] = (
                    f"'{message['sds_type']}' not supported. Please create an issue at https://github.com/moehrem/tetraconnect/issues"
                )
                raise ValueError

    def _self_process_short_location_report_88(
        self, frame_data: dict, message: dict
    ) -> None:
        """Process Short Location Report type 10 in +CTSDSR message.

        Args:
            frame_data (dict): Parsed frame data including user_data.

        Returns:
            None: Updated frame data with Short Location Report specific fields.

        """

        # hex to binary string
        user_data_hex = frame_data.get("user_data", "")
        bin_string = bin(int(user_data_hex, 16))[2:].zfill(4 * len(user_data_hex))

        # Extract data
        # sds_type_bin = bin_string[0:8]  # 8
        pdu_type_bin = bin_string[8:10]  # 2
        time_elapsed_bin = bin_string[10:12]  # 2
        lng_bin = bin_string[12:37]  # 25
        lat_bin = bin_string[37:61]  # 24
        position_error_bin = bin_string[61:64]  # 3
        horizontal_velocity_bin = bin_string[64:71]  # 7
        travel_direction_bin = bin_string[71:75]  # 4
        type_add_data_bin = bin_string[75:76]  # 1
        reason_sending_bin = bin_string[76:84]  # 8
        user_def_data_bin = bin_string[84:92]  # 8

        # map extracted data to descriptions
        pdu_type = self.mappings.pdu_type_desc(int(pdu_type_bin, 2))
        time_elapsed = self.mappings.time_elapsed_desc(int(time_elapsed_bin, 2))
        position_error = self.mappings.position_error_desc(position_error_bin)
        direction = self.mappings.direction_desc(travel_direction_bin)
        reason_sending = self.mappings.reason_sending_desc(int(reason_sending_bin, 2))
        type_add_data = self.mappings.type_add_data_desc(int(type_add_data_bin, 2))

        # add to message
        message["pdu_type"] = pdu_type
        message["time_elapsed"] = time_elapsed
        message["position_error"] = position_error
        message["direction"] = direction
        message["reason_sending"] = reason_sending
        message["type_add_data"] = type_add_data
        message["user_defined_data"] = int(user_def_data_bin, 2)

        # convert lat/lng to signed values
        # lng
        try:
            lng_bin = int(lng_bin, 2)
            if lng_bin >= 2**24:
                lng_bin -= 2**25
            message["lng"] = lng_bin * (360 / 2**25)
        except ValueError:
            message["lng"] = None

        # lat
        try:
            lat_bin = int(lat_bin, 2)
            if lat_bin >= 2**23:
                lat_bin -= 2**24
            message["lat"] = lat_bin * (180 / 2**24)
        except ValueError:
            message["lat"] = None

        # convert horizontal velocity to km/h
        try:
            horizontal_velocity_bin = int(horizontal_velocity_bin, 2)
            if horizontal_velocity_bin < 28:
                message["velocity"] = horizontal_velocity_bin
            elif 28 <= horizontal_velocity_bin < 127:
                message["velocity"] = round(
                    16 * (1 + 0.038) ** (horizontal_velocity_bin - 13)
                )
            else:
                message["velocity"] = "unknown"
        except ValueError:
            message["velocity"] = "unknown"

    def _self_process_short_location_report_168(
        self, frame_data: dict, message: dict
    ) -> None:
        """Process extended Short Location Report type 10 in +CTSDSR message.

        Sometimes Motorola sends an extended Short Location Report with 168 bytes instead of the standard 88 bytes.
        There is no public documentation available for this extended format. As the last 51 bytes seem to be vendor-specific data,
        we can not decode them properly at this time. The first 88 bytes are processed as per ETSI TS 100 392-18-1 V1.7.2 (2018-01).

        Args:
            frame_data (dict): Parsed frame data including user_data.

        Returns:
            None: Updated frame data with extended Short Location Report specific fields.

        """

        ## hex to binary string
        user_data_hex = frame_data.get("user_data", "")
        bin_string = bin(int(user_data_hex, 16))[2:].zfill(4 * len(user_data_hex))

        pos_bit = 0

        ## extract and mad basic fields
        # sds_type = bin_string[0:8]  # 8
        pos_bit += 8

        pdu_type = bin_string[pos_bit : pos_bit + 2]  # 2
        pdu_type_ext = bin_string[pos_bit + 2 : pos_bit + 6]  # 4

        message["pdu_type"] = self.mappings.pdu_type_desc(int(pdu_type, 2))
        message["pdu_type_extension"] = self.mappings.pdu_type_ext_desc(
            int(pdu_type_ext, 2)
        )

        pos_bit += 14

        ## extract and map time data
        time_type = bin_string[pos_bit : pos_bit + 2]  # 2
        pos_bit += 2

        match int(time_type, 2):
            case 0:  # no time stamp
                pos_bit += 0
            case 1:  # time elapsed
                time_elapsed = bin_string[pos_bit : pos_bit + 2]  # 2
                message["time_elapsed"] = self.mappings.time_elapsed_desc(
                    int(time_elapsed, 2)
                )

                pos_bit += 2

            case 2:  # time of position
                # time_of_position = bin_string[16:38]  # 22
                day = bin_string[pos_bit : pos_bit + 5]  # 5
                hour = bin_string[pos_bit + 5 : pos_bit + 10]  # 5
                minute = bin_string[pos_bit + 10 : pos_bit + 16]  # 6
                second = bin_string[pos_bit + 16 : pos_bit + 22]  # 6

                message["time_of_position"] = {
                    "day": int(day, 2),
                    "hour": int(hour, 2),
                    "minute": int(minute, 2),
                    "second": int(second, 2),
                }

                pos_bit += 22

            case _:  # reserved
                _LOGGER.warning(
                    "Unsupported time type in Motorola extended Short Location Report: %s",
                    time_type,
                )
                frame_data["error"]["Unsupported time type"] = (
                    f"Time type '{time_type}' not supported. Please create an issue at https://github.com/moehrem/tetraconnect/issues"
                )
                raise ValueError

        ## extract location data
        location_shape = bin_string[pos_bit : pos_bit + 4]  # 4
        pos_bit += 4

        match int(location_shape, 2):
            case 0:  # no shape
                pos_bit += 0
            case 1:  # location point, 49 bits
                longitude = bin_string[pos_bit : pos_bit + 25]  # 25
                latitude = bin_string[pos_bit + 25 : pos_bit + 49]  # 24

                message["longitude"] = int(longitude, 2) * (360 / 2**25)
                message["latitude"] = int(latitude, 2) * (180 / 2**24)

                pos_bit += 49

            case 2:  # location circle, 55 bits
                longitude = bin_string[pos_bit : pos_bit + 25]  # 25
                latitude = bin_string[pos_bit + 25 : pos_bit + 49]  # 24
                horizontal_position_uncert = bin_string[
                    pos_bit + 49 : pos_bit + 55
                ]  # 6

                message["longitude"] = int(longitude, 2) * (360 / 2**25)
                message["latitude"] = int(latitude, 2) * (180 / 2**24)
                message["horizontal_position_uncertainty"] = (
                    2 * (1 + 0.2) ** (int(horizontal_position_uncert, 2) + 5)
                ) - 4

                pos_bit += 55

            case 3:  # location ellipse, 72 bits
                longitude = bin_string[pos_bit : pos_bit + 25]  # 25
                latitude = bin_string[pos_bit + 25 : pos_bit + 49]  # 24
                half_of_major_axis = bin_string[pos_bit + 49 : pos_bit + 55]  # 6
                half_of_minor_axis = bin_string[pos_bit + 55 : pos_bit + 61]  # 6
                angle = bin_string[pos_bit + 61 : pos_bit + 69]  # 8
                confidence_level = bin_string[pos_bit + 69 : pos_bit + 72]  # 3

                message["longitude"] = int(longitude, 2) * (360 / 2**25)
                message["latitude"] = int(latitude, 2) * (180 / 2**24)
                message["half_of_major_axis"] = (
                    2 * (1 + 0.2) ** (int(half_of_major_axis, 2) + 5)
                ) - 4
                message["half_of_minor_axis"] = (
                    2 * (1 + 0.2) ** (int(half_of_minor_axis, 2) + 5)
                ) - 4
                message["angle"] = int(angle, 2) * (360 / 256)
                message["confidence_level"] = self.mappings.confidence_level_desc(
                    int(confidence_level, 2)
                )

                pos_bit += 72

            case 4:  # location point with alltitude, 61 bits
                longitude = bin_string[pos_bit : pos_bit + 25]  # 25
                latitude = bin_string[pos_bit + 25 : pos_bit + 49]  # 24
                location_altitude_type = bin_string[pos_bit + 49 : pos_bit + 50]  # 1
                location_altitude = bin_string[pos_bit + 50 : pos_bit + 61]  # 11

                message["longitude"] = int(longitude, 2) * (360 / 2**25)
                message["latitude"] = int(latitude, 2) * (180 / 2**24)
                message["location_altitude_type"] = (
                    self.mappings.location_altitude_type_desc(
                        int(location_altitude_type, 2)
                    )
                )
                message["location_altitude"] = (
                    self.mappings.location_altitude_calculation(
                        int(location_altitude, 2)
                    )
                )

                pos_bit += 61

            case 5:  # location circle with altitude, 67 bits
                longitude = bin_string[pos_bit : pos_bit + 25]  # 25
                latitude = bin_string[pos_bit + 25 : pos_bit + 49]  # 24
                horizontal_position_uncert = bin_string[
                    pos_bit + 49 : pos_bit + 55
                ]  # 6
                location_altitude_type = bin_string[pos_bit + 55 : pos_bit + 56]  # 1
                location_altitude = bin_string[pos_bit + 56 : pos_bit + 67]  # 11

                message["longitude"] = int(longitude, 2) * (360 / 2**25)
                message["latitude"] = int(latitude, 2) * (180 / 2**24)
                message["horizontal_position_uncertainty"] = (
                    2 * (1 + 0.2) ** (int(horizontal_position_uncert, 2) + 5)
                ) - 4
                message["location_altitude_type"] = (
                    self.mappings.location_altitude_type_desc(
                        int(location_altitude_type, 2)
                    )
                )
                message["location_altitude"] = (
                    self.mappings.location_altitude_calculation(
                        int(location_altitude, 2)
                    )
                )

                pos_bit += 67

            case 6:  # location ellipse with altitude, 84 bits
                longitude = bin_string[pos_bit : pos_bit + 25]  # 25
                latitude = bin_string[pos_bit + 25 : pos_bit + 49]  # 24
                half_of_major_axis = bin_string[pos_bit + 49 : pos_bit + 55]  # 6
                half_of_minor_axis = bin_string[pos_bit + 55 : pos_bit + 61]  # 6
                angle = bin_string[pos_bit + 61 : pos_bit + 69]  # 8
                location_altitude_type = bin_string[pos_bit + 69 : pos_bit + 70]  # 1
                location_altitude = bin_string[pos_bit + 70 : pos_bit + 81]  # 11
                confidence_level = bin_string[pos_bit + 81 : pos_bit + 84]  # 3

                message["longitude"] = int(longitude, 2) * (360 / 2**25)
                message["latitude"] = int(latitude, 2) * (180 / 2**24)
                message["half_of_major_axis"] = (
                    2 * (1 + 0.2) ** (int(half_of_major_axis, 2) + 5)
                ) - 4
                message["half_of_minor_axis"] = (
                    2 * (1 + 0.2) ** (int(half_of_minor_axis, 2) + 5)
                ) - 4
                message["angle"] = int(angle, 2) * (360 / 256)
                message["location_altitude_type"] = (
                    self.mappings.location_altitude_type_desc(
                        int(location_altitude_type, 2)
                    )
                )
                message["location_altitude"] = (
                    self.mappings.location_altitude_calculation(
                        int(location_altitude, 2)
                    )
                )
                message["confidence_level"] = self.mappings.confidence_level_desc(
                    int(confidence_level, 2)
                )

                pos_bit += 84

            case 7:  # Location circle with altitude and altitude uncertainty, 70 bits
                longitude = bin_string[pos_bit : pos_bit + 25]  # 25
                latitude = bin_string[pos_bit + 25 : pos_bit + 49]  # 24
                horizontal_position_uncert = bin_string[
                    pos_bit + 49 : pos_bit + 55
                ]  # 6
                location_altitude_type = bin_string[pos_bit + 55 : pos_bit + 56]  # 1
                location_altitude = bin_string[pos_bit + 56 : pos_bit + 67]  # 11
                altitude_uncertainty = bin_string[pos_bit + 67 : pos_bit + 70]  # 3

                message["longitude"] = int(longitude, 2) * (360 / 2**25)
                message["latitude"] = int(latitude, 2) * (180 / 2**24)
                message["horizontal_position_uncertainty"] = (
                    2 * (1 + 0.2) ** (int(horizontal_position_uncert, 2) + 5)
                ) - 4
                message["location_altitude_type"] = (
                    self.mappings.location_altitude_type_desc(
                        int(location_altitude_type, 2)
                    )
                )
                message["location_altitude"] = (
                    self.mappings.location_altitude_calculation(
                        int(location_altitude, 2)
                    )
                )
                message["altitude_uncertainty"] = (
                    2 * (1 + 0.2) ** (int(altitude_uncertainty, 2) + 5)
                ) - 4

                pos_bit += 70

            case 8:  # Location ellipse with altitude and altitude uncertainty, 87 bits
                longitude = bin_string[pos_bit : pos_bit + 25]  # 25
                latitude = bin_string[pos_bit + 25 : pos_bit + 49]  # 24
                half_of_major_axis = bin_string[pos_bit + 49 : pos_bit + 55]  # 6
                half_of_minor_axis = bin_string[pos_bit + 55 : pos_bit + 61]  # 6
                angle = bin_string[pos_bit + 61 : pos_bit + 69]  # 8
                location_altitude_type = bin_string[pos_bit + 69 : pos_bit + 70]  # 1
                location_altitude = bin_string[pos_bit + 70 : pos_bit + 81]  # 11
                location_altitude_accuracy = bin_string[
                    pos_bit + 81 : pos_bit + 84
                ]  # 3
                confidence_level = bin_string[pos_bit + 84 : pos_bit + 87]  # 3

                message["longitude"] = int(longitude, 2) * (360 / 2**25)
                message["latitude"] = int(latitude, 2) * (180 / 2**24)
                message["half_of_major_axis"] = (
                    2 * (1 + 0.2) ** (int(half_of_major_axis, 2) + 5)
                ) - 4
                message["half_of_minor_axis"] = (
                    2 * (1 + 0.2) ** (int(half_of_minor_axis, 2) + 5)
                ) - 4
                message["angle"] = int(angle, 2) * (360 / 256)
                message["location_altitude_type"] = (
                    self.mappings.location_altitude_type_desc(
                        int(location_altitude_type, 2)
                    )
                )
                message["location_altitude"] = (
                    self.mappings.location_altitude_calculation(
                        int(location_altitude, 2)
                    )
                )
                message["location_altitude_accuracy"] = (
                    self.mappings.location_altitude_accuracy_desc(
                        int(location_altitude_accuracy, 2)
                    )
                )
                message["confidence_level"] = self.mappings.confidence_level_desc(
                    int(confidence_level, 2)
                )

                pos_bit += 87

            case 9:  # Location arc, 100 bits
                longitude = bin_string[pos_bit : pos_bit + 25]  # 25
                latitude = bin_string[pos_bit + 25 : pos_bit + 49]  # 24
                inner_radius = bin_string[pos_bit + 49 : pos_bit + 65]  # 16
                outer_radius = bin_string[pos_bit + 65 : pos_bit + 81]  # 16
                start_angle = bin_string[pos_bit + 81 : pos_bit + 89]  # 8
                stop_angle = bin_string[pos_bit + 89 : pos_bit + 97]  # 8
                confidence_level = bin_string[pos_bit + 97 : pos_bit + 100]  # 3

                message["longitude"] = int(longitude, 2) * (360 / 2**25)
                message["latitude"] = int(latitude, 2) * (180 / 2**24)
                message["inner_radius"] = int(inner_radius, 2) * 2  # in meters
                message["outer_radius"] = int(outer_radius, 2) * 2  # in meters
                message["start_angle"] = int(start_angle, 2) * (360 / 256)
                message["stop_angle"] = int(stop_angle, 2) * (360 / 256)
                message["confidence_level"] = self.mappings.confidence_level_desc(
                    int(confidence_level, 2)
                )

                pos_bit += 100

            case 10:  # Location point and position error, 52 bits
                longitude = bin_string[pos_bit : pos_bit + 25]  # 25
                latitude = bin_string[pos_bit + 25 : pos_bit + 49]  # 24
                position_error = bin_string[pos_bit + 49 : pos_bit + 52]  # 3

                message["longitude"] = int(longitude, 2) * (360 / 2**25)
                message["latitude"] = int(latitude, 2) * (180 / 2**24)
                message["position_error"] = self.mappings.position_error_desc(
                    position_error
                )

                pos_bit += 52

            case 11:  # Reserved
                pass

            case 12:  # Reserved
                pass

            case 13:  # Reserved
                pass

            case 14:  # Reserved
                pass

            case 15:  # Location shape extension, 4 bits
                location_shape_extension = bin_string[pos_bit : pos_bit + 4]  # 4

                message["location_shape_extension"] = int(location_shape_extension, 2)

                pos_bit += 4

            case _:  # unsupported
                _LOGGER.warning(
                    "Unsupported location shape in Motorola extended Short Location Report: %s",
                    location_shape,
                )
                frame_data["error"]["Unsupported location shape"] = (
                    f"Location shape '{location_shape}' not supported. Please create an issue at https://github.com/moehrem/tetraconnect/issues"
                )
                raise ValueError

        ## extract and map velocity data
        velocity_type = bin_string[pos_bit : pos_bit + 3]  # 3
        pos_bit += 3

        match int(velocity_type, 2):
            case 0:  # no velocity
                pos_bit += 0
            case 1:  # horizontal velocity, 7 bits
                horizontal_velocity = bin_string[pos_bit : pos_bit + 7]  # 7

                message["horizontal_velocity"] = (
                    16 * (1 + 0.038) ** (int(horizontal_velocity, 2) - 13) + 0
                )

                pos_bit += 7

            case 2:  # horizontal velocity with uncertainty, 10 bits
                horizontal_velocity = bin_string[pos_bit : pos_bit + 7]  # 7
                horizontal_velocity_uncertainty = bin_string[
                    pos_bit + 7 : pos_bit + 10
                ]  # 3

                message["horizontal_velocity"] = (
                    16 * (1 + 0.038) ** (int(horizontal_velocity, 2) - 13) + 0
                )
                message["horizontal_velocity_uncertainty"] = (
                    self.mappings.horizontal_velocity_uncertainty_desc(
                        int(horizontal_velocity_uncertainty, 2)
                    )
                )

                pos_bit += 10

            case 3:  # horizontal velocity and vertical velocity, 15 bits
                horizontal_velocity = bin_string[pos_bit : pos_bit + 7]  # 7
                vertical_velocity_sign = bin_string[pos_bit + 7 : pos_bit + 8]  # 1
                vertical_velocity = bin_string[pos_bit + 8 : pos_bit + 15]  # 7

                message["horizontal_velocity"] = (
                    16 * (1 + 0.038) ** (int(horizontal_velocity, 2) - 13) + 0
                )
                message["vertical_velocity_sign"] = (
                    self.mappings.vertical_velocity_sign_desc(
                        int(vertical_velocity_sign, 2)
                    )
                )
                message["vertical_velocity"] = (
                    self.mappings.vertical_velocity_calculation(
                        int(vertical_velocity, 2)
                    )
                )

            case (
                4
            ):  # horizontal velocity and vertical velocity with uncertainty, 21 bits
                horizontal_velocity = bin_string[pos_bit : pos_bit + 7]  # 7
                horizontal_velocity_uncertainty = bin_string[
                    pos_bit + 7 : pos_bit + 10
                ]  # 3
                vertical_velocity_sign = bin_string[pos_bit + 10 : pos_bit + 11]  # 1
                vertical_velocity = bin_string[pos_bit + 11 : pos_bit + 18]  # 7
                vertical_velocity_uncertainty = bin_string[
                    pos_bit + 18 : pos_bit + 21
                ]  # 3

                message["horizontal_velocity"] = (
                    16 * (1 + 0.038) ** (int(horizontal_velocity, 2) - 13) + 0
                )
                message["horizontal_velocity_uncertainty"] = (
                    self.mappings.horizontal_velocity_uncertainty_desc(
                        int(horizontal_velocity_uncertainty, 2)
                    )
                )
                message["vertical_velocity_sign"] = (
                    self.mappings.vertical_velocity_sign_desc(
                        int(vertical_velocity_sign, 2)
                    )
                )
                message["vertical_velocity"] = (
                    self.mappings.vertical_velocity_calculation(
                        int(vertical_velocity, 2)
                    )
                )
                message["vertical_velocity_uncertainty"] = (
                    self.mappings.vertical_velocity_uncertainty_desc(
                        int(vertical_velocity_uncertainty, 2)
                    )
                )

                pos_bit += 21

            case 5:  # horizontal velocity with direction of travel extended, 15 bits
                horizontal_velocity = bin_string[pos_bit : pos_bit + 7]  # 7
                direction_of_travel_extended = bin_string[
                    pos_bit + 7 : pos_bit + 15
                ]  # 8

                message["horizontal_velocity"] = (
                    16 * (1 + 0.038) ** (int(horizontal_velocity, 2) - 13) + 0
                )
                message["direction_of_travel_extended"] = int(
                    direction_of_travel_extended, 2
                ) * (360 / 256)

                pos_bit += 15

            case 6:  # horizontal velocity with direction of travel extended and uncertainty, 21 bits
                horizontal_velocity = bin_string[pos_bit : pos_bit + 7]  # 7
                horizontal_velocity_uncertainty = bin_string[
                    pos_bit + 7 : pos_bit + 10
                ]  # 3
                direction_of_travel_extended = bin_string[
                    pos_bit + 10 : pos_bit + 18
                ]  # 8
                direction_of_travel_extended_uncertainty = bin_string[
                    pos_bit + 18 : pos_bit + 21
                ]  # 3

                message["horizontal_velocity"] = (
                    16 * (1 + 0.038) ** (int(horizontal_velocity, 2) - 13) + 0
                )
                message["horizontal_velocity_uncertainty"] = (
                    self.mappings.horizontal_velocity_uncertainty_desc(
                        int(horizontal_velocity_uncertainty, 2)
                    )
                )
                message["direction_of_travel_extended"] = int(
                    direction_of_travel_extended, 2
                ) * (360 / 256)
                message["direction_of_travel_extended_uncertainty"] = (
                    self.mappings.direction_of_travel_uncertainty_desc(
                        int(direction_of_travel_extended_uncertainty, 2)
                    )
                )

                pos_bit += 21

            case 7:  # horizontal velocity and vertical velocity with direction of travel extended and uncertainty, 32 bits
                horizontal_velocity = bin_string[pos_bit : pos_bit + 7]  # 7
                horizontal_velocity_uncertainty = bin_string[pos_bit + 7 : pos_bit + 10]
                vertical_velocity_sign = bin_string[pos_bit + 10 : pos_bit + 11]  # 1
                vertical_velocity = bin_string[pos_bit + 11 : pos_bit + 18]  # 7
                vertical_velocity_uncertainty = bin_string[
                    pos_bit + 18 : pos_bit + 21
                ]  # 3
                direction_of_travel_extended = bin_string[
                    pos_bit + 21 : pos_bit + 29
                ]  # 8
                direction_of_travel_extended_uncertainty = bin_string[
                    pos_bit + 29 : pos_bit + 32
                ]  # 3

                message["horizontal_velocity"] = (
                    16 * (1 + 0.038) ** (int(horizontal_velocity, 2) - 13) + 0
                )
                message["horizontal_velocity_uncertainty"] = (
                    self.mappings.horizontal_velocity_uncertainty_desc(
                        int(horizontal_velocity_uncertainty, 2)
                    )
                )
                message["vertical_velocity_sign"] = (
                    self.mappings.vertical_velocity_sign_desc(
                        int(vertical_velocity_sign, 2)
                    )
                )
                message["vertical_velocity"] = (
                    self.mappings.vertical_velocity_calculation(
                        int(vertical_velocity, 2)
                    )
                )
                message["vertical_velocity_uncertainty"] = (
                    self.mappings.vertical_velocity_uncertainty_desc(
                        int(vertical_velocity_uncertainty, 2)
                    )
                )
                message["direction_of_travel_extended"] = int(
                    direction_of_travel_extended, 2
                ) * (360 / 256)
                message["direction_of_travel_extended_uncertainty"] = (
                    self.mappings.direction_of_travel_uncertainty_desc(
                        int(direction_of_travel_extended_uncertainty, 2)
                    )
                )

                pos_bit += 32

            case _:  # unknown
                _LOGGER.warning(
                    "Unsupported velocity type in Motorola extended Short Location Report: %s",
                    velocity_type,
                )
                frame_data["error"]["Unsupported velocity type"] = (
                    f"Velocity type '{velocity_type}' not supported. Please create an issue at https://github.com/moehrem/tetraconnect/issues"
                )
                raise ValueError

        ## extract and map remaining mandatory fields
        acknowledgment_request = bin_string[pos_bit : pos_bit + 1]  # 1
        type_add_data = bin_string[pos_bit + 1 : pos_bit + 2]  # 1
        reason_sending = bin_string[pos_bit + 2 : pos_bit + 10]  # 8

        message["acknowledgment_request"] = self.mappings.acknowledgment_request_desc(
            int(acknowledgment_request, 2)
        )
        message["type_add_data"] = self.mappings.type_add_data_desc(
            int(type_add_data, 2)
        )
        message["reason_sending"] = self.mappings.reason_sending_desc(
            int(reason_sending, 2)
        )

        pos_bit += 10

        ## end of mandatory fields
        ## rest of the data for motorola extension
        motorola_extension_blob = bin_string[pos_bit:]

        message["motorola_extension_blob"] = hex(int(motorola_extension_blob, 2))

    def _self_process_status_report(self, frame_data: dict, message: dict) -> None:
        """Process Status Report type 128 in +CTSDSR message.

        Args:
            frame_data (dict): Parsed frame data including user_data.
            message (dict): Message dictionary to be updated.

        Returns:
            None: Updated frame data with Status Report specific fields.

        """

        # hex to binary string
        user_data_hex = frame_data.get("user_data", "")

        # Extract data
        status_code = int(user_data_hex[2:4]) - 2

        # add to message
        message["status_code"] = status_code

    def _process_encr(self, frame_data: dict, message: dict) -> None:
        """Process +ENCR message.

        Args:
            frame_data (dict): Parsed frame data including user_data.
            message (dict): Message dictionary to be updated.

        Returns:
            None: Updated frame data with encryption indication.

        """

        if self.working_header is None:
            return

        data = self.working_header

        message["ai_service"] = int(data[1]) if len(data) > 1 else None
        message["opta"] = data[2] if len(data) > 2 else None
