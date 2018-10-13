"""Test cyton module."""
import pytest
from openbci_interface import cyton

# pylint: disable=protected-access,invalid-name

pytestmark = pytest.mark.cyton


def test_attributes():
    """Cyton board has 8 EEG channels and 3 AUX channels"""
    assert cyton.Cyton.num_eeg == 8
    assert cyton.Cyton.num_aux == 3


@pytest.mark.cyton_command_set
class TestCytonCommandSet:
    """Test Cyton SDK commands

    http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set
    """
    ###########################################################################
    # Turn on/off channel
    @staticmethod
    @pytest.mark.parametrize('channel,command', [
        (1, b'!'),
        (2, b'@'),
        (3, b'#'),
        (4, b'$'),
        (5, b'%'),
        (6, b'^'),
        (7, b'&'),
        (8, b'*'),
    ])
    def test_enable_channel(cyton_mock, channel, command):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(command, None)]
        cyton_mock.board.enable_channel(channel)
        assert cyton_mock.board.channel_configs[channel-1].enabled

    @staticmethod
    @pytest.mark.parametrize('channel,command', [
        (1, b'1'),
        (2, b'2'),
        (3, b'3'),
        (4, b'4'),
        (5, b'5'),
        (6, b'6'),
        (7, b'7'),
        (8, b'8'),
    ])
    def test_disable_channel(cyton_mock, channel, command):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(command, None)]
        cyton_mock.board.disable_channel(channel)
        assert not cyton_mock.board.channel_configs[channel-1].enabled

    ###########################################################################
    # Default channel settings
    @staticmethod
    def test_channels_default(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [
            (b'd', b'updating channel settings to default$$$')]
        cyton_mock.board.set_channels_default()

    @staticmethod
    def test_get_default_settings(cyton_mock):
        expected = '060110'
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [
            (b'D', b'%s$$$' % expected.encode('utf-8'))]
        found = cyton_mock.board.get_default_settings()
        assert found == expected

    ###########################################################################
    # Streaming
    @staticmethod
    def test_start_streaming(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b'b', None)]
        cyton_mock.board.start_streaming()

    @staticmethod
    def test_start_streaming_wifi(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b'b', b'Stream started$$$')]
        cyton_mock.board.wifi_attached = True
        cyton_mock.board.start_streaming()

    @staticmethod
    def test_stop_streaming(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b's', None)]
        cyton_mock.board.stop_streaming()

    @staticmethod
    def test_stop_streaming_wifi(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b's', b'Stream stopped$$$')]
        cyton_mock.board.wifi_attached = True
        cyton_mock.board.stop_streaming()

    ###########################################################################
    # Misc
    @staticmethod
    def test_reset(cyton_mock, init_message):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b'v', init_message)]
        cyton_mock.board.reset()


@pytest.mark.cyton_v2_command_set
class TestCytonV2CommandSet:
    """Test Cyton V2.0.0 new commands
    http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v200-new-commands
    """
    ###########################################################################
    # Timestamp
    @staticmethod
    def test_enable_timestamp_streaming(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b'<', None)]
        cyton_mock.board.streaming = True
        cyton_mock.board.enable_timestamp()

    @staticmethod
    def test_enable_timestamp(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b'<', b'Time stamp ON$$$')]
        cyton_mock.board.enable_timestamp()

    @staticmethod
    def test_disable_timestamp_streaming(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b'>', None)]
        cyton_mock.board.streaming = True
        cyton_mock.board.disable_timestamp()

    @staticmethod
    def test_disable_timestamp(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b'>', b'Time stamp OFF$$$')]
        cyton_mock.board.disable_timestamp()


@pytest.mark.cyton_v3_command_set
class TestCytonV3CommandSet:
    """Test Cyton V3.0.0 new commands

    http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands
    """
    ###########################################################################
    # Sample Rate
    @staticmethod
    @pytest.mark.parametrize('sample_rate', [
        250, 500, 1000, 2000, 4000, 8000, 16000,
    ])
    def test_get_sample_rate(cyton_mock, sample_rate):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [
            (b'~~', b'Success: Sample rate is %dHz$$$' % sample_rate)]
        found = cyton_mock.board.get_sample_rate()
        assert found == sample_rate

    @staticmethod
    @pytest.mark.parametrize('sample_rate,pattern', [
        (250, (b'~6', b'Success: Sample rate is 250Hz$$$')),
        (500, (b'~5', b'Success: Sample rate is 500Hz$$$')),
        (1000, (b'~4', b'Success: Sample rate is 1000Hz$$$')),
        (2000, (b'~3', b'Success: Sample rate is 2000Hz$$$')),
        (4000, (b'~2', b'Success: Sample rate is 4000Hz$$$')),
        (8000, (b'~1', b'Success: Sample rate is 8000Hz$$$')),
        (16000, (b'~0', b'Success: Sample rate is 16000Hz$$$')),
    ])
    def test_set_sample_rate(cyton_mock, sample_rate, pattern):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [pattern]
        found = cyton_mock.board.set_sample_rate(sample_rate)
        assert found == sample_rate

    ###########################################################################
    # Board Mode
    @staticmethod
    @pytest.mark.parametrize('mode', [
        'default', 'debug', 'analog', 'digital', 'marker',
    ])
    def test_get_board_mode(cyton_mock, mode):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [
            (b'//', b'Board mode is %s$$$' % mode.encode('utf-8'))
        ]
        found = cyton_mock.board.get_board_mode()
        assert mode == found

    @staticmethod
    @pytest.mark.parametrize('mode,pattern', [
        ('default', (b'/0', b'Success: default$$$')),
        ('debug', (b'/1', b'Success: debug$$$')),
        ('analog', (b'/2', b'Success: analog$$$')),
        ('digital', (b'/3', b'Success: digital$$$')),
        ('marker', (b'/4', b'Success: marker$$$')),
    ])
    def test_set_board_mode(cyton_mock, mode, pattern):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [pattern]
        cyton_mock.board.set_board_mode(mode)

    ###########################################################################
    # WiFi
    @staticmethod
    def test_attach_wifi_success(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b'{', b'Success: Wifi attached$$$')]
        cyton_mock.board.attach_wifi()

    @staticmethod
    def test_attach_wifi_failure(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b'{', b'Failure: Wifi not attached$$$')]
        with pytest.raises(RuntimeError):
            cyton_mock.board.attach_wifi()

    @staticmethod
    def test_detach_wifi_success(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b'}', b'Success: Wifi removed$$$')]
        cyton_mock.board.wifi_attached = True
        cyton_mock.board.detach_wifi()

    @staticmethod
    def test_detach_wifi_failure(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b'}', b'Failure: Wifi not removed$$$')]
        cyton_mock.board.wifi_attached = True
        with pytest.raises(RuntimeError):
            cyton_mock.board.detach_wifi()

    @staticmethod
    def test_get_wifi_status_present(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b':', b'Wifi present$$$')]
        cyton_mock.board.wifi_attached = True
        cyton_mock.board.get_wifi_status()

    @staticmethod
    def test_get_wifi_status_not_present(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [
            (b':', b'Wifi not present, send { to attach the shield$$$')]
        cyton_mock.board.get_wifi_status()

    @staticmethod
    def test_reset_wifi(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b';', b'Wifi soft reset$$$')]
        cyton_mock.board.reset_wifi()

    ###########################################################################
    # Others
    @staticmethod
    def test_get_version(cyton_mock):
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(b'V', b'v3.1.1$$$')]
        cyton_mock.board.get_firmware_version()


@pytest.mark.cyton_context_manager
class TestCytonContextManager:
    """Context Manager
    """
    @staticmethod
    def test_context_manager(cyton_patch, init_message):
        cyton_patch.serial.patterns = [
            (b'v', init_message),
            (b'b', None),
            (b's', None),
        ]
        with cyton_patch.board as board:
            board.start_streaming()
        assert not cyton_patch.serial.is_open

    @staticmethod
    def test_context_manager_opened(cyton_mock, init_message):
        """Passing an open Serial instance keeps serial opened at exit"""
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [
            (b'v', init_message),
        ]
        with cyton_mock.board:
            pass
        assert cyton_mock.serial.is_open

    @staticmethod
    def test_context_manager_closed(cyton_mock, init_message):
        """Passing a closed Serial instance will close connection at exit"""
        cyton_mock.serial.patterns = [
            (b'v', init_message),
        ]
        with cyton_mock.board:
            pass
        assert not cyton_mock.serial.is_open


@pytest.mark.cyton_sample_acquisition
class TestCytonReadSample:
    """Sample Acquisition
    """
    @staticmethod
    def test_read_sample_0xC0(cyton_mock):
        """Test acquisition of standard sample with accel"""
        cyton_mock.serial.open()
        cyton_mock.serial.patterns = [(
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
        )]
        expected = {
            'eeg': [
                -68601.57175082824,
                -73968.47146373648,
                -70592.24046376234,
                -71232.26031449561,
                -71844.11696721519,
                4942.730658379872,
                4884.169087906967,
                4922.59173662564,
            ],
            'aux': [0.054, 0.226, 0.92],
            'packet_id': 119,
            'timestamp': None,
        }
        cyton_mock.board.start_streaming()
        sample = cyton_mock.board.read_sample()

        assert sample.keys() == expected.keys()

        for key in sample:
            if key != 'timestamp':
                assert sample[key] == expected[key]
