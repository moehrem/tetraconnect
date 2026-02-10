---
name: Bug Report
about: Create a report to help us improve Tetraconnect
title: "[BUG] "
labels: bug
assignees: ""
---

## Bug Description

**Describe the bug**
A clear and concise description of what the bug is.

**Expected behavior**
A clear and concise description of what you expected to happen.

**Actual behavior**
A clear and concise description of what actually happened.

## Steps to Reproduce

1. Go to '...'
2. Click on '....'
3. Configure '....'
4. See error

## Environment Information

**Tetraconnect Integration Version:**

- Version: [e.g. 1.2.3]

**TETRA Device Information:**

- Manufacturer: [e.g. Motorola, Sepura]
- Model: [e.g. MTP850, STP9000]
- Firmware version: [if known]
- Connection: [Serial port, USB, etc.]

## Log Information

**Home Assistant Core Log:**

```
# Please include relevant log entries from Home Assistant
# Go to Settings > System > Logs and filter for "tetraconnect"
# Or check /config/home-assistant.log

[timestamp] ERROR (MainThread) [custom_components.tetraconnect] ...
```

**Debug Logs (if available):**

```
# Enabled debug logging for tetraconnect, reproduce the issue, disable debug logging.
# You'll receive a textfile with all and very helpful information. That includes
# logging and radio communication details! Thus please check the file before uploading!
```

## Screenshots/Additional Context

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Serial Communication**
If the issue relates to serial communication, please include:

- Are you receiving any data from the TETRA device?
- Does the device respond to AT commands manually?
- Any specific TETRA commands or messages involved?

**MQTT Information**
If the issue relates to events, please include:

- Are events fired? Please check log and developer options -> events.

**Additional context**
Anything else that might help?

## Troubleshooting Attempted

- [ ] Restarted Home Assistant
- [ ] Checked serial cable/connection
- [ ] Verified TETRA device is responding
- [ ] Checked Home Assistant logs
- [ ] Tried different baudrate/serial settings
- [ ] Tested MQTT broker connectivity
- [ ] Reinstalled the integration

## Possible Solution

If you have any ideas on how to fix the issue, please describe them here.
