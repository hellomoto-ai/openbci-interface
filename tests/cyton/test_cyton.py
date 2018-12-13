"""Test cyton module."""
import pytest
from openbci_interface import cyton, exception

from tests import messages

# pylint: disable=protected-access,invalid-name

pytestmark = pytest.mark.cyton


def test_attributes():
    """Cyton board has 8 EEG channels and 3 AUX channels"""
    board = cyton.Cyton(None)
    assert board.num_aux == 3
    board.daisy_attached = False
    assert board.num_eeg == 8
    board.daisy_attached = True
    assert board.num_eeg == 16


@pytest.mark.parametrize(
    'sample_rate',
    [250, 500, 1000, 2000, 4000, 8000, 16000]
)
def test_cycle(sample_rate):
    """Cyton acquisition cycle is halved when Daisy is attached"""
    board = cyton.Cyton(None)
    board.sample_rate = sample_rate
    board.daisy_attached = False
    assert board.cycle == 1 / sample_rate
    board.daisy_attached = True
    assert board.cycle == 1 / sample_rate * 2


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
        cyton_mock._serial.patterns = [(command, None)]
        cyton_mock.enable_channel(channel)
        assert cyton_mock.channel_configs[channel-1].enabled

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
        cyton_mock._serial.patterns = [(command, None)]
        cyton_mock.disable_channel(channel)
        assert not cyton_mock.channel_configs[channel-1].enabled

    ###########################################################################
    # Configure Channel Command
    @staticmethod
    @pytest.mark.parametrize(
        'channel,channel_code', [
            (1, b'1'),
            (2, b'2'),
            (3, b'3'),
            (4, b'4'),
            (5, b'5'),
            (6, b'6'),
            (7, b'7'),
            (8, b'8'),
            (9, b'Q'),
            (10, b'W'),
            (11, b'E'),
            (12, b'R'),
            (13, b'T'),
            (14, b'Y'),
            (15, b'U'),
            (16, b'I'),
        ])
    @pytest.mark.parametrize(
        'power_down,power_down_code', [
            ('ON', b'0'),
            # ('OFF', b'1'),
        ])
    @pytest.mark.parametrize(
        'gain,gain_code', [
            # (1, b'0'),
            # (2, b'1'),
            # (4, b'2'),
            # (6, b'3'),
            # (8, b'4'),
            # (12, b'5'),
            (24, b'6'),
        ])
    @pytest.mark.parametrize(
        'input_type,input_type_code', [
            ('NORMAL', b'0'),
            # ('SHORTED', b'1'),
            # ('BIAS_MEAS', b'2'),
            # ('MVDD', b'3'),
            # ('TEMP', b'4'),
            # ('TESTSIG', b'5'),
            # ('BIAS_DRP', b'6'),
            # ('BIAS_DRN', b'7'),
        ])
    @pytest.mark.parametrize(
        'bias,bias_code', [
            # (0, b'0'),
            (1, b'1'),
        ])
    @pytest.mark.parametrize(
        'srb2,srb2_code', [
            # (0, b'0'),
            (1, b'1'),
        ])
    @pytest.mark.parametrize(
        'srb1,srb1_code', [
            (0, b'0'),
            # (1, b'1'),
        ])
    def test_configure_channel(
            cyton_mock,
            channel, channel_code,
            power_down, power_down_code,
            gain, gain_code,
            input_type, input_type_code,
            bias, bias_code,
            srb2, srb2_code,
            srb1, srb1_code,
    ):
        cfg = cyton_mock.channel_configs[channel - 1]
        assert cfg.power_down is None
        assert cfg.gain is None
        assert cfg.input_type is None
        assert cfg.bias is None
        assert cfg.srb2 is None
        assert cfg.srb1 is None

        command = b''.join([
            b'x',
            channel_code, power_down_code, gain_code,
            input_type_code, bias_code, srb2_code, srb1_code,
            b'X'])
        cyton_mock._serial.patterns = [(command, None)]
        cyton_mock.streaming = True
        cyton_mock.configure_channel(
            channel=channel, power_down=power_down,
            gain=gain, input_type=input_type, bias=bias, srb2=srb2, srb1=srb1)

        assert cfg.power_down == power_down
        assert cfg.gain == gain
        assert cfg.input_type == input_type
        assert cfg.bias == bias
        assert cfg.srb2 == srb2
        assert cfg.srb1 == srb1

    ###########################################################################
    # Default channel settings
    @staticmethod
    def test_channels_default(cyton_mock):
        cyton_mock._serial.patterns = [(b'd', messages.RESET_CHANNEL)]
        cyton_mock.reset_channels()

    @staticmethod
    def test_get_default_settings(cyton_mock):
        cyton_mock._serial.patterns = [(b'D', b'060110$$$')]
        found = cyton_mock.get_default_settings()
        expected = {
            'power_down': 'ON',
            'gain': 24,
            'input_type': 'NORMAL',
            'bias': 1,
            'srb2': 1,
            'srb1': 0,
        }
        assert found == expected

    ###########################################################################
    # Streaming
    @staticmethod
    def test_start_streaming(cyton_mock):
        cyton_mock._serial.patterns = [(b'b', None)]
        cyton_mock.start_streaming()

    @staticmethod
    def test_start_streaming_wifi(cyton_mock):
        cyton_mock._serial.patterns = [(b'b', messages.STREAM_STARTED)]
        cyton_mock.wifi_attached = True
        cyton_mock.start_streaming()

    @staticmethod
    def test_stop_streaming(cyton_mock):
        cyton_mock._serial.patterns = [(b's', None)]
        cyton_mock.stop_streaming()

    @staticmethod
    def test_stop_streaming_wifi(cyton_mock):
        cyton_mock._serial.patterns = [(b's', messages.STREAM_STOPPED)]
        cyton_mock.wifi_attached = True
        cyton_mock.stop_streaming()

    ###########################################################################
    # Misc
    @staticmethod
    def test_reset_board(cyton_mock):
        cyton_mock._serial.patterns = [(b'v', messages.CYTON_V3_INFO)]
        cyton_mock.reset_board()
        assert not cyton_mock.daisy_attached

    @staticmethod
    def test_reset_board_daisy(cyton_mock):
        cyton_mock._serial.patterns = [(b'v', messages.CYTON_V3_WITH_DAISY_INFO)]
        cyton_mock.reset_board()
        assert cyton_mock.daisy_attached


@pytest.mark.cyton_16_channel_command_set
class TestCyton16ChannelCommandSet:
    """Test 16 CHANNEL COMMANDS
    http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-16-channel-commands
    """
    @staticmethod
    def test_attach_daisy_alread_attached(cyton_mock):
        cyton_mock._serial.patterns = [(b'C', messages.DAISY_ALREADY_ATTACHED)]
        cyton_mock.attach_daisy()
        assert cyton_mock.daisy_attached

    @staticmethod
    def test_attach_daisy_attached(cyton_mock):
        cyton_mock._serial.patterns = [(b'C', messages.DAISY_ATTACHED)]
        cyton_mock.attach_daisy()
        assert cyton_mock.daisy_attached

    @staticmethod
    def test_attach_daisy_not_attached(cyton_mock):
        cyton_mock._serial.patterns = [(b'C', messages.NO_DAISY_TO_ATTACH)]
        cyton_mock.attach_daisy()
        assert not cyton_mock.daisy_attached

    @staticmethod
    def test_detach_daisy_present(cyton_mock):
        cyton_mock._serial.patterns = [(b'c', messages.DAISY_REMOVED)]
        cyton_mock.daisy_attached = True
        cyton_mock.detach_daisy()
        assert not cyton_mock.daisy_attached

    @staticmethod
    def test_detach_daisy_not_present(cyton_mock):
        cyton_mock._serial.patterns = []
        cyton_mock.daisy_attached = False
        cyton_mock.wifi_attached = False
        cyton_mock.detach_daisy()
        assert not cyton_mock.daisy_attached

    @staticmethod
    def test_detach_daisy_not_present_wifi(cyton_mock):
        cyton_mock._serial.patterns = []
        cyton_mock.daisy_attached = False
        cyton_mock.wifi_attached = True
        cyton_mock.detach_daisy()
        assert not cyton_mock.daisy_attached


@pytest.mark.cyton_v2_command_set
class TestCytonV2CommandSet:
    """Test Cyton V2.0.0 new commands
    http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v200-new-commands
    """
    ###########################################################################
    # Timestamp
    @staticmethod
    def test_enable_timestamp_streaming(cyton_mock):
        cyton_mock._serial.patterns = [(b'<', None)]
        cyton_mock.streaming = True
        cyton_mock.enable_timestamp()

    @staticmethod
    def test_enable_timestamp(cyton_mock):
        cyton_mock._serial.patterns = [(b'<', messages.TIMESTAMP_ON)]
        cyton_mock.enable_timestamp()

    @staticmethod
    def test_disable_timestamp_streaming(cyton_mock):
        cyton_mock._serial.patterns = [(b'>', None)]
        cyton_mock.streaming = True
        cyton_mock.disable_timestamp()

    @staticmethod
    def test_disable_timestamp(cyton_mock):
        cyton_mock._serial.patterns = [(b'>', messages.TIMESTAMP_OFF)]
        cyton_mock.disable_timestamp()


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
        cyton_mock._serial.patterns = [
            (b'~~', b'Success: Sample rate is %dHz$$$' % sample_rate)]
        found = cyton_mock.get_sample_rate()
        assert found == sample_rate

    @staticmethod
    @pytest.mark.parametrize('sample_rate,pattern', [
        (250, (b'~6', messages.SAMPLE_RATE_250)),
        (500, (b'~5', messages.SAMPLE_RATE_500)),
        (1000, (b'~4', messages.SAMPLE_RATE_1000)),
        (2000, (b'~3', messages.SAMPLE_RATE_2000)),
        (4000, (b'~2', messages.SAMPLE_RATE_4000)),
        (8000, (b'~1', messages.SAMPLE_RATE_8000)),
        (16000, (b'~0', messages.SAMPLE_RATE_16000)),
    ])
    def test_set_sample_rate(cyton_mock, sample_rate, pattern):
        cyton_mock._serial.patterns = [pattern]
        found = cyton_mock.set_sample_rate(sample_rate)
        assert found == sample_rate

    ###########################################################################
    # Board Mode
    @staticmethod
    @pytest.mark.parametrize('mode', [
        'default', 'debug', 'analog', 'digital', 'marker',
    ])
    def test_get_board_mode(cyton_mock, mode):
        cyton_mock._serial.patterns = [
            (b'//', b'Board mode is %s$$$' % mode.encode('utf-8'))
        ]
        found = cyton_mock.get_board_mode()
        assert mode == found

    @staticmethod
    @pytest.mark.parametrize('mode,pattern', [
        ('default', (b'/0', messages.BOARD_MODE_DEFAULT)),
        ('debug', (b'/1', messages.BOARD_MODE_DEBUG)),
        ('analog', (b'/2', messages.BOARD_MODE_ANALOG)),
        ('digital', (b'/3', messages.BOARD_MODE_DIGITAL)),
        ('marker', (b'/4', messages.BOARD_MODE_MARKER)),
    ])
    def test_set_board_mode(cyton_mock, mode, pattern):
        cyton_mock._serial.patterns = [pattern]
        cyton_mock.set_board_mode(mode)
        assert cyton_mock.board_mode == mode

    ###########################################################################
    # WiFi
    @staticmethod
    def test_attach_wifi_success(cyton_mock):
        cyton_mock._serial.patterns = [(b'{', messages.WIFI_ATTACH_SUCCESS)]
        cyton_mock.attach_wifi()
        assert cyton_mock.wifi_attached

    @staticmethod
    def test_attach_wifi_failure(cyton_mock):
        cyton_mock._serial.patterns = [(b'{', messages.WIFI_ATTACH_FAILURE)]
        with pytest.raises(RuntimeError):
            cyton_mock.attach_wifi()

    @staticmethod
    def test_detach_wifi_success(cyton_mock):
        cyton_mock._serial.patterns = [(b'}', messages.WIFI_REMOVE_SUCCESS)]
        cyton_mock.wifi_attached = True
        cyton_mock.detach_wifi()
        assert not cyton_mock.wifi_attached

    @staticmethod
    def test_detach_wifi_failure(cyton_mock):
        cyton_mock._serial.patterns = [(b'}', messages.WIFI_REMOVE_FAILURE)]
        cyton_mock.wifi_attached = True
        with pytest.raises(RuntimeError):
            cyton_mock.detach_wifi()
        assert cyton_mock.wifi_attached

    @staticmethod
    def test_get_wifi_status_present(cyton_mock):
        cyton_mock._serial.patterns = [(b':', messages.WIFI_PRESENT)]
        cyton_mock.wifi_attached = False
        cyton_mock.get_wifi_status()
        assert cyton_mock.wifi_attached

    @staticmethod
    def test_get_wifi_status_not_present(cyton_mock):
        cyton_mock._serial.patterns = [(b':', messages.WIFI_NOT_PRESENT)]
        cyton_mock.wifi_attached = True
        cyton_mock.get_wifi_status()
        assert not cyton_mock.wifi_attached

    @staticmethod
    def test_reset_wifi(cyton_mock):
        cyton_mock._serial.patterns = [(b';', messages.WIFI_RESET)]
        cyton_mock.reset_wifi()

    ###########################################################################
    # Others
    @staticmethod
    def test_get_version(cyton_mock):
        cyton_mock._serial.patterns = [(b'V', b'v3.1.1$$$')]
        cyton_mock.get_firmware_version()


@pytest.mark.cyton_context_manager
class TestCytonContextManager:
    """Context Manager
    """
    @staticmethod
    def test_context_manager(cyton_mock):
        """`initialize` is called on __enter__"""
        cyton_mock._serial.patterns = [
            (b'v', messages.CYTON_V3_INFO),
            (b'V', b'Firmware: v3.1.1$$$'),
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
        ]
        with cyton_mock:
            pass

    @staticmethod
    def test_context_manager_streaming(cyton_mock):
        """Streaming is stopped automatically"""
        cyton_mock._serial.patterns = [
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
            (b'b', None),
            (b's', None),
        ]
        with cyton_mock as board:
            board.start_streaming()

    @staticmethod
    def test_context_manager_daisy(cyton_mock):
        """16 channels are initialized when Daisy"""
        cyton_mock._serial.patterns = [
            (b'v', messages.CYTON_V3_WITH_DAISY_INFO),
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
            (b'Q', None), (b'xQ060110X', messages.SET_CHANNEL_9),
            (b'W', None), (b'xW060110X', messages.SET_CHANNEL_10),
            (b'E', None), (b'xE060110X', messages.SET_CHANNEL_11),
            (b'R', None), (b'xR060110X', messages.SET_CHANNEL_12),
            (b'T', None), (b'xT060110X', messages.SET_CHANNEL_13),
            (b'Y', None), (b'xY060110X', messages.SET_CHANNEL_14),
            (b'U', None), (b'xU060110X', messages.SET_CHANNEL_15),
            (b'I', None), (b'xI060110X', messages.SET_CHANNEL_16),
        ]
        with cyton_mock:
            pass


@pytest.mark.cyton_sample_acquisition
class TestCytonReadSample:
    """Sample Acquisition
    """
    @staticmethod
    def test_read_sample_0xC0(cyton_mock):
        """Test acquisition of standard sample with accel"""
        for cfg in cyton_mock.channel_configs:
            cfg.gain = 24
        cyton_mock._serial.patterns = [(
            b'b',
            # Packet
            b'\xa0'          # Start byte
            b'w'             # Packet ID
            b'\x00\x00\x00'  # EEG 1
            b'\x00\x00\x00'  # EEG 2
            b'\x00\x00\x00'  # EEG 3
            b'\x00\x00\x00'  # EEG 4
            b'\x00\x00\x00'  # EEG 5
            b'\x00\x00\x00'  # EEG 6
            b'\x00\x00\x00'  # EEG 7
            b'\x00\x00\x00'  # EEG 8
            b'\x00\x00'      # AUX 1
            b'\x00\x00'      # AUX 2
            b'\x00\x00'      # AUX 3
            b'\xc0'          # Stop byte
        )]
        expected = {
            'eeg': [0.0] * 8,
            'aux': [0.0] * 3,
            'raw_eeg': [0] * 8,
            'raw_aux': [0] * 3,
            'packet_id': 119,
            'timestamp': None,
            'valid': True,
        }
        cyton_mock.start_streaming()
        sample = cyton_mock.read_sample()

        assert sample.keys() == expected.keys()

        for key in sample:
            if key != 'timestamp':
                assert sample[key] == expected[key]

    @staticmethod
    def test_read_sample_0xC0_daisy(cyton_mock):
        """Test acquisition of standard sample with accel"""
        for cfg in cyton_mock.channel_configs:
            cfg.gain = 24
        cyton_mock._serial.patterns = [(
            b'b',
            # Packet 1
            b'\xa0'          # Start byte
            b'w'             # Packet ID
            b'\x00\x00\x00'  # EEG 1
            b'\x00\x00\x00'  # EEG 2
            b'\x00\x00\x00'  # EEG 3
            b'\x00\x00\x00'  # EEG 4
            b'\x00\x00\x00'  # EEG 5
            b'\x00\x00\x00'  # EEG 6
            b'\x00\x00\x00'  # EEG 7
            b'\x00\x00\x00'  # EEG 8
            b'\x00\x00'      # AUX 1
            b'\x00\x00'      # AUX 2
            b'\x00\x00'      # AUX 3
            b'\xc0'          # Stop byte
            # Packet 2
            b'\xa0'          # Start byte
            b'x'             # Packet ID
            b'\x00\x00\x00'  # EEG 9
            b'\x00\x00\x00'  # EEG 10
            b'\x00\x00\x00'  # EEG 11
            b'\x00\x00\x00'  # EEG 12
            b'\x00\x00\x00'  # EEG 13
            b'\x00\x00\x00'  # EEG 14
            b'\x00\x00\x00'  # EEG 15
            b'\x00\x00\x00'  # EEG 16
            b'\x00\x00'      # AUX 1
            b'\x00\x00'      # AUX 2
            b'\x00\x00'      # AUX 3
            b'\xc0'          # Stop byte
        )]
        expected = {
            'eeg': [0.0] * 16,
            'aux': [0.0] * 3,
            'raw_eeg': [0] * 16,
            'raw_aux': [0] * 3,
            'packet_id': 119,
            'timestamp': None,
            'valid': True,
        }
        cyton_mock.daisy_attached = True
        cyton_mock.start_streaming()
        sample = cyton_mock.read_sample()

        assert sample.keys() == expected.keys()

        for key in sample:
            if key != 'timestamp':
                assert sample[key] == expected[key]

    @staticmethod
    def test_read_sample_0xC1(cyton_mock):
        """Test acquisition of standard sample with accel"""
        for cfg in cyton_mock.channel_configs:
            cfg.gain = 24
        cyton_mock._serial.patterns = [(
            b'b',
            b'\xa0'          # Start byte
            b'w'             # Packet ID
            b'\x00\x00\x00'  # EEG 1
            b'\x00\x00\x00'  # EEG 2
            b'\x00\x00\x00'  # EEG 3
            b'\x00\x00\x00'  # EEG 4
            b'\x00\x00\x00'  # EEG 5
            b'\x00\x00\x00'  # EEG 6
            b'\x00\x00\x00'  # EEG 7
            b'\x00\x00\x00'  # EEG 8
            b'\x00\x00'      # AUX 1
            b'\x00\x00'      # AUX 2
            b'\x00\x00'      # AUX 3
            b'\xc1'          # Stop byte
        )]
        expected = {
            'eeg': [0.0] * 8,
            'aux': [0.0] * 3,
            'raw_eeg': [0] * 8,
            'raw_aux': [0] * 3,
            'packet_id': 119,
            'timestamp': None,
            'valid': False,
        }
        cyton_mock.start_streaming()
        sample = cyton_mock.read_sample()

        assert sample.keys() == expected.keys()

        for key in sample:
            if key != 'timestamp':
                assert sample[key] == expected[key]

    @staticmethod
    def test_read_sample_timeout(cyton_mock):
        """read_sample raises SampleAcquisitionTimeout when timeout occurs."""
        cyton_mock._serial.patterns = [(
            b'b',
            b'w'  # Random value to be skipped
            b''   # Emulate timeout with empty response
        )]
        cyton_mock.start_streaming()
        with pytest.raises(exception.SampleAcquisitionTimeout):
            cyton_mock.read_sample()


class TestCytonConfigIO:
    """Configuration seliarazation"""
    @staticmethod
    def test_get_configs(cyton_mock):
        """Test get configuration"""
        cyton_mock._serial.patterns = [
            (b'v', messages.CYTON_V3_WITH_DAISY_INFO),
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
            (b'Q', None), (b'xQ060110X', messages.SET_CHANNEL_9),
            (b'W', None), (b'xW060110X', messages.SET_CHANNEL_10),
            (b'E', None), (b'xE060110X', messages.SET_CHANNEL_11),
            (b'R', None), (b'xR060110X', messages.SET_CHANNEL_12),
            (b'T', None), (b'xT060110X', messages.SET_CHANNEL_13),
            (b'Y', None), (b'xY060110X', messages.SET_CHANNEL_14),
            (b'U', None), (b'xU060110X', messages.SET_CHANNEL_15),
            (b'I', None), (b'xI060110X', messages.SET_CHANNEL_16),
        ]
        with cyton_mock:
            configs = cyton_mock.get_config()
            default_configs = {
                'board_mode': 'default',
                'sample_rate': 250,
                'channels': [{
                    'enabled': True,
                    'parameters': {
                        'power_down': 'ON',
                        'gain': 24,
                        'input_type': 'NORMAL',
                        'bias': 1,
                        'srb2': 1,
                        'srb1': 0,
                    },
                }] * 16,
            }
            assert default_configs == configs
