# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Connection status binary sensor with CONNECTIVITY device class
- Structured buffer management with `PersistentBuffer` and `WorkingBuffer` dataclasses
- Short aliases for buffer access (`self.wb`, `self.pb`) for improved code readability
- Comprehensive coordinator refactoring for better separation of concerns

### Changed

- **BREAKING**: Updated dependency from `pyserial-asyncio` to `pyserial-asyncio-fast` for better performance
- **BREAKING**: Connection status sensor refactored as binary sensor (on/off) instead of text state
  - Simplifies automations and UI representation
  - `connected` → on, `reconnecting`/`disconnected` → off
  - Internal diagnostics still log full status through logging
- Major coordinator architecture refactoring:
  - Moved all data processing logic from `Coordinator` to `DataHandler`
  - Coordinator now minimal: only 3 lines in `handle_serial_data()`
  - Introduced structured buffer management with dataclasses
  - Separated persistent state (`PersistentBuffer`) from temporary working state (`WorkingBuffer`)
- Enhanced data handler organization:
  - Single orchestration method `data_handler()` that calls pipeline steps
  - Each processing step (decode, parse, check, manufacturer, incomplete, fire) isolated in own method
  - Optimized `_fire_events()` method to eliminate code duplication
  - Improved error handling with specific exception catching
- Improved code organization:
  - Better separation of concerns between modules
  - Cleaner method responsibilities
  - More maintainable and testable architecture

### Fixed

- Resolved dependency deprecation warning for pyserial-asyncio
- Fixed data handler state management with proper buffer isolation
- Improved handling of incomplete messages with persistent buffer

### Removed

- Unused `update_entities()` method from helpers (dead code)
- Redundant exception variable in incomplete message handling

## [0.3.13] - 2024-07-31

### Changed

- Updated manifest version
- Minor stability improvements

## [0.3.12] - 2024-07-29

### Added

- Dynamic manufacturer handler system
- Improved data processing pipeline with dedicated DataHandler class
- Enhanced coordinator architecture for better data flow
- Support for raw message categorization (complete, incomplete, invalid)

### Changed

- Restructured data handling from SerialHandler to Coordinator
- Improved separation between serial communication and data processing
- Enhanced manufacturer-specific message handling

### Fixed

- Resolved issues with message buffer management
- Improved handling of multi-line TETRA messages
- Fixed entity update reliability

## [0.3.11] - 2024-07-28

### Added

- MQTT publishing functionality for TETRA data
- Configurable MQTT broker connectivity
- MQTT topic customization in config flow
- Dedicated MQTT publishing methods in helpers

### Changed

- Separated MQTT logic from entity update methods
- Improved helpers class structure and organization
- Enhanced config flow with MQTT configuration options

### Fixed

- Resolved MQTT publishing reliability issues
- Fixed config flow translation handling

## [0.3.10] - 2024-07-27

### Added

- Enhanced config flow with improved device detection
- Better error handling for serial connection failures
- Improved TETRA device initialization process
- Support for custom TETRA service profile selection

### Changed

- Improved serial connection stability and retry logic
- Enhanced device information parsing during config flow
- Better timeout handling for device communication

### Fixed

- Fixed serial connection timeout issues
- Resolved device detection problems in config flow
- Improved handling of incomplete TETRA responses

## [0.3.9] - 2024-07-26

### Added

- Comprehensive TETRA message parsing for Motorola devices
- Support for location data (GPS coordinates, velocity, direction)
- Status message handling with proper state mapping
- Error code translation for TETRA CME errors

### Changed

- Improved Motorola message handler with better data extraction
- Enhanced coordinate calculation for location services
- Better handling of binary data in TETRA messages

### Fixed

- Fixed coordinate conversion algorithms for proper GPS positioning
- Resolved issues with velocity and direction calculations
- Improved error handling for malformed TETRA messages

## [0.3.8] - 2024-07-25

### Added

- Serial connection monitoring and auto-reconnection
- Configurable retry attempts and connection timeouts
- Connection status reporting via dedicated entities
- Improved logging for serial communication debugging

### Changed

- Enhanced COM manager with robust connection lifecycle
- Improved serial protocol handling with better error recovery
- Better separation of connection management and data processing

### Fixed

- Fixed serial connection stability issues
- Resolved problems with connection loss detection
- Improved handling of device disconnection scenarios

## [0.3.7] - 2024-07-24

### Added

- Multi-manufacturer support architecture
- Motorola device support with full message parsing
- TETRA command mapping and response handling
- Device identification and capability detection

### Changed

- Restructured codebase for manufacturer-specific handlers
- Improved message parsing with manufacturer-specific logic
- Enhanced device detection during configuration

### Fixed

- Fixed manufacturer-specific message format handling
- Resolved issues with device identification
- Improved TETRA command response parsing

## [0.3.6] - 2024-07-23

### Added

- Home Assistant config flow implementation
- Serial port auto-detection and selection
- Device manufacturer selection in setup wizard
- Automatic device information retrieval

### Changed

- Migrated from YAML configuration to UI-based setup
- Improved user experience with guided configuration
- Enhanced serial port discovery and filtering

### Fixed

- Fixed config flow validation and error handling
- Resolved issues with serial port permissions
- Improved device detection reliability

## [0.3.5] - 2024-07-22

### Added

- Basic TETRA device communication support
- Serial interface connection management
- Initial Motorola device support
- Entity creation for TETRA data

### Changed

- Implemented coordinator pattern for data management
- Improved entity lifecycle management
- Enhanced error handling and logging

### Fixed

- Fixed serial communication initialization
- Resolved entity state update issues
- Improved error recovery mechanisms

## [0.3.0] - 2024-07-20

### Added

- Initial release of Tetraconnect integration
- Basic TETRA radio communication support
- Serial interface connectivity
- Sensor entity creation for TETRA data
- Home Assistant integration framework

### Features

- Connect to TETRA radios via serial interface
- Real-time TETRA message decoding
- Support for Motorola TETRA devices
- Entity-based data representation
- Configurable serial communication parameters

### Requirements

- Home Assistant 2024.1.0 or later
- Serial access to TETRA device
- Python 3.11+ with pyserial-asyncio

## [0.2.0] - 2024-07-15

### Added

- Project structure and basic framework
- Initial Motorola device support planning
- Serial communication architecture design
- Home Assistant integration scaffolding

## [0.1.0] - 2024-07-10

### Added

- Initial project creation
- Basic project documentation
- License and contributing guidelines
- Repository structure setup

---

## Version History Summary

- **0.3.x Series**: Major feature development with MQTT support, dynamic handlers, and enhanced data processing
- **0.2.x Series**: Foundation building and architecture design
- **0.1.x Series**: Project initialization and planning

## Upgrade Notes

### From 0.3.11 to 0.3.12

- The data handling architecture has been significantly refactored
- Manufacturer handlers now use dynamic loading
- No configuration changes required, but restart recommended

### From 0.3.10 to 0.3.11

- MQTT functionality added - configure MQTT settings in integration options
- No breaking changes to existing entities

### From 0.3.9 to 0.3.10

- Enhanced config flow may require reconfiguration for better device detection
- Existing configurations remain compatible

## Breaking Changes

### 0.3.0

- Initial release - no previous versions to consider

## Security Notes

- Always ensure TETRA data sources are legally accessible
- Integration does not support encrypted TETRA message decoding
- Serial communication requires appropriate system permissions

## Acknowledgments

- Based on ETSI EN 300 392‑5 V2.7.1 (April 2020) standards
- Community contributions and testing
- Home Assistant development team for framework support
