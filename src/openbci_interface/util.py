"""Module to implement utility functions."""
import re
import logging

import serial
import serial.tools.list_ports

from openbci_interface import cyton, exception

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
    _LG.debug('Found %d COM ports.', len(devices))
    for device in devices:
        msg = _get_firmware_string(device, timeout=timeout)
        _LG.debug('Message: %s', repr(msg))
        if re.search(filter_regex, msg):
            yield device
        elif 'Device failed to poll Host' in msg:
            _LG.warning(
                'Found USB dongle at "%s", '
                'but it failed to poll message from a board; %s',
                device, repr(msg)
            )


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


def _is_cyton(message):
    return 'ADS1299' in message


def _is_ganglion(message):
    return 'Ganglion' in message


def wrap(serial_obj):
    """Autodetect board-type and return serial wrapper for the type detected.

    Parameters
    ----------
    serial_obj : serial.Serial
        Serial instance with open connection

    Returns
    -------
    Board
        Serial wrapper for detected board.
        :func:`Cyton<openbci_interface.cyton.Cyton>` for cyton board.

        Other boards are not supported yet.

    Raises
    ------
    Message validation error
        See :func:`validate_message()<openbci_interface.util.validate_message>`

    :class:`NotSupported<openbci_interface.exception.NotSupported>`
        Unsupported or unknown board type.
    """
    serial_obj.write(b'v')
    message = serial_obj.read_until(b'$$$').decode('utf-8', errors='ignore')
    _LG.debug(repr(message))

    validate_message(message)

    if _is_ganglion(message):
        _LG.info('Detected Ganglion board %s.', serial_obj.port)
        raise exception.NotSupported('Ganglion')

    if _is_cyton(message):
        _LG.info('Detected Cyton board %s.', serial_obj.port)
        return cyton.Cyton(serial_obj)

    raise exception.NotSupported('Unkonwn')
