"""Module to implement utility functions."""
import re
import logging

import serial
import serial.tools.list_ports

from openbci_interface import exception

_LG = logging.getLogger(__name__)


def _get_firmware_string(port, timeout=2):
    _LG.debug('Checking port: %s', port)
    with serial.Serial(port=port, baudrate=115200, timeout=timeout) as ser:
        ser.write(b'v')
        return ser.read_until(b'$$$').decode('utf-8', errors='ignore')


def list_devices(filter_regex='OpenBCI', timeout=2):
    """List OpenBCI devices by querying COM ports.

    Parameters
    ----------
    filter_regex : str
        Regular expression applied to firmware information string,
        using ``re.search`` function. To get only Cyton boards, you can
        use ``ADS1299``. To get only Ganglion, you can use ``Gangion``.

    timeout : float
        Read timeout

    Yields
    ------
    str
        Name of the device found.
    """
    devices = [p.device for p in serial.tools.list_ports.comports()]
    _LG.info('Found %d COM ports. %s', len(devices), devices)
    for device in devices:
        msg = _get_firmware_string(device, timeout=timeout)
        if 'Device failed to poll Host' in msg:
            _LG.error(
                'Found USB dongle at "%s", '
                'but it failed to poll message from a board; %s',
                device, repr(msg)
            )
        elif re.search(filter_regex, msg):
            _LG.info('Matched   [%s] %s "%s"', filter_regex, device, msg)
            yield device
        else:
            _LG.info('Unmatched [%s] %s "%s"', filter_regex, device, msg)


def validate_message(message):
    """Validate message received from serial.

    Raises
    ------
    :class:`UnexpectedMessageFormat<openbci_interface.exception.UnexpectedMessageFormat>`
        Message does not end with ``$$$``.

    :class:`DeviceNotConnected<openbci_interface.exception.DeviceNotConnected>`
        Serial connection is working, but no board is avaialable.
    """
    if not message.endswith('$$$'):
        raise exception.UnexpectedMessageFormat(message)
    if 'Device failed to poll Host' in message:
        raise exception.DeviceNotConnected(message)
