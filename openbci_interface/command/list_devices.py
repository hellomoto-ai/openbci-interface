"""Implements ``list_devices`` command."""
import sys
import time
import logging

from serial import Serial
from serial.tools.list_ports import comports

_LG = logging.getLogger(__name__)


def _is_openbci_device(port):
    _LG.debug('Checking port: %s', port)
    with Serial(port=port, baudrate=115200, timeout=1) as ser:
        try:
            ser.write(b'v')
            time.sleep(2)
            message = ser.read_until(b'$$$').decode('utf-8', errors='ignore')
        except Exception:  # pylint: disable=broad-except
            return False
        if message:
            for msg in message.split('\n'):
                _LG.debug('    %s', msg)
        return 'OpenBCI' in message


def _get_ports():
    ports = [comport.device for comport in comports()]
    _LG.debug('Found %d ports.', len(ports))
    for port in ports:
        if _is_openbci_device(port):
            yield port


def main(_):
    """Entrypoint for ``list_devices`` command.

    For the detail of the command, use ``list_devices --help``.
    """
    for port in _get_ports():
        sys.stdout.write(port)
        sys.stdout.write('\n')
