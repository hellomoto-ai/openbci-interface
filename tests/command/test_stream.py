from openbci_interface.command import stream_

from tests import messages
from tests.serial_mock import SerialMock as BaseSerialMock


class SerialMock(BaseSerialMock):
    _patterns = iter([
        (b'v', messages.CYTON_V3_INFO),
        (b'V', b'v3.1.1$$$'),
        (b'/0', messages.BOARD_MODE_DEFAULT),
        (b'~6', messages.SAMPLE_RATE_250),
        (b'D', b'060110$$$'),
        (b'!', None), (b'x1060110X', messages.SET_CHANNEL_1),
        (b'@', None), (b'x2060110X', messages.SET_CHANNEL_2),
        (b'#', None), (b'x3060110X', messages.SET_CHANNEL_3),
        (b'$', None), (b'x4060110X', messages.SET_CHANNEL_4),
        (b'%', None), (b'x5060110X', messages.SET_CHANNEL_5),
        (b'^', None), (b'x6060110X', messages.SET_CHANNEL_6),
        (b'&', None), (b'x7060110X', messages.SET_CHANNEL_7),
        (b'*', None), (b'x8060110X', messages.SET_CHANNEL_8),
        (b'/0', messages.BOARD_MODE_DEFAULT),
        (b'~6', messages.SAMPLE_RATE_250),
        (
            b'b',
            b'\xa0'          # Start byte
            b'w'             # Packet ID
            b'\xd1+\x02'     # EEG 1
            b'\xcd\x81\x13'  # EEG 2
            b'\xcf\xcf\x1d'  # EEG 3
            b'\xcf_C'        # EEG 4
            b'\xce\xf4U'     # EEG 5
            b'\x03_\xce'     # EEG 6
            b'\x03U\x92'     # EEG 7
            b'\x03\\I'       # EEG 8
            b'\x01\xb0'      # AUX 1
            b'\x07\x10'      # AUX 2
            b'\x1c\xc0'      # AUX 3
            b'\xc0'          # Stop byte
        ),
        (b's', None),
    ])


def _raise_kbi():
    raise KeyboardInterrupt('')


def test_stream(mocker):
    """Test ``stream`` command"""
    mocker.patch(
        'openbci_interface.command.stream_.Serial', SerialMock)
    mocker.patch(
        'openbci_interface.command.stream_.sys.stdout.flush', _raise_kbi)
    stream_.main(['--port', 'foo'])
    mocker.resetall()