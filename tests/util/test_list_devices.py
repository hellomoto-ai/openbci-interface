from collections import namedtuple

import pytest

from openbci_interface import util

from . import conftest

pytestmark = [pytest.mark.util, pytest.mark.util_list_devices]


def _comports():
    Port = namedtuple('ComPort', ['device'])
    return [Port(device) for device in conftest.SerialMock.firmware_strings]


@pytest.mark.parametrize('filter_pattern,expected', [
    (
        'Ganglion',
        ['ganglion_v2'],
    ),
    (
        'ADS1299',
        ['cyton_8bit', 'cyton_v1', 'cyton_v2', 'cyton_v3', 'daisy_v3'],
    ),
    (
        'OpenBCI',
        [
            'cyton_8bit', 'cyton_v1', 'cyton_v2', 'cyton_v3',
            'daisy_v3', 'ganglion_v2',
        ],
    ),
])
def test_list_devices(mocker, filter_pattern, expected):
    mocker.patch.object(util.serial, 'Serial', conftest.SerialMock)
    mocker.patch.object(util.serial.tools.list_ports, 'comports', _comports)

    found = util.list_devices(filter_pattern)
    assert sorted(found) == sorted(expected)
