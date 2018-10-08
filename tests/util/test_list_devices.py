from collections import namedtuple

import pytest

from openbci_interface import util

pytestmark = pytest.mark.util


class SerialMock:
    """Mock Serial Device"""
    firmware_strings = {
        'foo': b'',
        'bar': b'',
        'cyton_8bit': b'''OpenBCI V3 8bit Board
Setting ADS1299 Channel Values
ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
$$$''',
        'cyton_v1': b'''OpenBCI V3 16 channel
ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
$$$''',
        'cyton_v2': b'''OpenBCI V3 8-16 channel
ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
Firmware: v2.0.0
$$$''',
        'cyton_v3': b'''OpenBCI V3 8-16 channel
On Board ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
Firmware: v3.1.1
$$$''',
        'ganglion_v2': b'''OpenBCI Ganglion v2.0.0
LIS2DH ID: 0x33
MCP3912 CONFIG_1: 0xXX
$$$'''
    }

    def __init__(self, port, baudrate, timeout):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self.buffer = None

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        pass

    def write(self, val):
        if val == b'v':
            self.buffer = SerialMock.firmware_strings[self.port]
        else:
            raise ValueError(
                '%s does not support `write` method with value `%s`'
                % (self.__class__.__name__, val)
            )

    def read_until(self, _):
        return self.buffer


def comports():
    Port = namedtuple('ComPort', ['device'])
    return [Port(device) for device in SerialMock.firmware_strings]


@pytest.mark.util_list_devices
@pytest.mark.parametrize('filter_pattern,expected', [
    (
        'Ganglion',
        ['ganglion_v2'],
    ),
    (
        'ADS1299',
        ['cyton_8bit', 'cyton_v1', 'cyton_v2', 'cyton_v3'],
    ),
    (
        'OpenBCI',
        ['cyton_8bit', 'cyton_v1', 'cyton_v2', 'cyton_v3', 'ganglion_v2'],
    ),
])
def test_list_devices(mocker, filter_pattern, expected):
    mocker.patch.object(util.serial, 'Serial', SerialMock)
    mocker.patch.object(util.serial.tools.list_ports, 'comports', comports)

    found = util.list_devices(filter_pattern)
    assert sorted(found) == sorted(expected)
