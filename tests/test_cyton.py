import pytest
from openbci_interface import cyton

from . import fixture

# pylint: disable=protected-access


def test_attributes():
    """Cyton board has 8 EEG channels and 3 AUX channels"""
    assert cyton.Cyton.num_eeg == 8
    assert cyton.Cyton.num_aux == 3


class BaseCytonTestSuite:
    def setup_method(self):
        """Setup Cyton board obj with Serial Mock"""
        # pylint: disable=attribute-defined-outside-init
        self.serial = fixture.SerialMock()
        self.board = cyton.Cyton(
            port='foo', timeout=0.1, serial_obj=self.serial)
        self.board.open()

    def teardown_method(self):
        """Check if all the IO patterns are consumed"""
        self.serial.validate_no_message_in_buffer()
        self.serial.validate_all_patterns_consumed()


class TestCommandSet(BaseCytonTestSuite):
    """Test Cyton SDK commands

    http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set
    """
    ###########################################################################
    # Default channel settings
    def test_channels_default(self):
        self.serial.patterns = [
            (b'd', b'updating channel settings to default$$$')]
        self.board.set_channels_default()

    def test_get_default_settings(self):
        expected = '060110'
        self.serial.patterns = [(b'D', b'%s$$$' % expected.encode('utf-8'))]
        found = self.board.get_default_settings()
        assert found == expected

    ###########################################################################
    # Streaming
    def test_start_streaming(self):
        self.serial.patterns = [(b'b', None)]
        self.board.start_streaming()

    def test_start_streaming_wifi(self):
        self.serial.patterns = [(b'b', b'Stream started$$$')]
        self.board._wifi_attached = True
        self.board.start_streaming()

    def test_stop_streaming(self):
        self.serial.patterns = [(b's', None)]
        self.board.stop_streaming()

    def test_stop_streaming_wifi(self):
        self.serial.patterns = [(b's', b'Stream stopped$$$')]
        self.board._wifi_attached = True
        self.board.stop_streaming()

    ###########################################################################
    # Misc
    def test_initialize(self):
        self.serial.patterns = [(b'v', b'''OpenBCI V3 8-16 channel
On Board ADS1299 Device ID: 0x3E
LIS3DH Device ID: 0x33
Firmware: v3.1.1
$$$''')]
        self.board.initialize()


class TestCytonV200Commands(BaseCytonTestSuite):
    """Test Cyton V2.0.0 new commands
    http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v200-new-commands
    """
    ###########################################################################
    # Timestamp
    def test_enable_timestamp_streaming(self):
        self.serial.patterns = [(b'<', None)]
        self.board._streaming = True
        self.board.enable_timestamp()

    def test_enable_timestamp(self):
        self.serial.patterns = [(b'<', b'Time stamp ON$$$')]
        self.board.enable_timestamp()

    def test_disable_timestamp_streaming(self):
        self.serial.patterns = [(b'>', None)]
        self.board._streaming = True
        self.board.disable_timestamp()

    def test_disable_timestamp(self):
        self.serial.patterns = [(b'>', b'Time stamp OFF$$$')]
        self.board.disable_timestamp()


class TestCytonV300Commands(BaseCytonTestSuite):
    """Test Cyton V3.0.0 new commands

    http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands
    """

    ###########################################################################
    # Sample Rate
    @pytest.mark.parametrize('sample_rate', [
        250, 500, 1000, 2000, 4000, 8000, 16000,
    ])
    def test_get_sample_rate(self, sample_rate):
        self.serial.patterns = [
            (b'~~', b'Success: Sample rate is %dHz$$$' % sample_rate)]
        found = self.board.get_sample_rate()
        assert found == sample_rate

    @pytest.mark.parametrize('sample_rate,pattern', [
        (250, (b'~6', b'Success: Sample rate is 250Hz$$$')),
        (500, (b'~5', b'Success: Sample rate is 500Hz$$$')),
        (1000, (b'~4', b'Success: Sample rate is 1000Hz$$$')),
        (2000, (b'~3', b'Success: Sample rate is 2000Hz$$$')),
        (4000, (b'~2', b'Success: Sample rate is 4000Hz$$$')),
        (8000, (b'~1', b'Success: Sample rate is 8000Hz$$$')),
        (16000, (b'~0', b'Success: Sample rate is 16000Hz$$$')),
    ])
    def test_set_sample_rate(self, sample_rate, pattern):
        self.serial.patterns = [pattern]
        found = self.board.set_sample_rate(sample_rate)
        assert found == sample_rate

    ###########################################################################
    # Board Mode
    @pytest.mark.parametrize('mode', [
        'default', 'debug', 'analog', 'digital', 'marker',
    ])
    def test_get_board_mode(self, mode):
        self.serial.patterns = [
            (b'//', b'Board mode is %s$$$' % mode.encode('utf-8'))
        ]
        found = self.board.get_board_mode()
        assert mode == found

    @pytest.mark.parametrize('mode,pattern', [
        ('default', (b'/0', b'Success: default$$$')),
        ('debug', (b'/1', b'Success: debug$$$')),
        ('analog', (b'/2', b'Success: analog$$$')),
        ('digital', (b'/3', b'Success: digital$$$')),
        ('marker', (b'/4', b'Success: marker$$$')),
    ])
    def test_set_board_mode(self, mode, pattern):
        self.serial.patterns = [pattern]
        self.board.set_board_mode(mode)

    ###########################################################################
    # WiFi
    def test_attach_wifi_success(self):
        self.serial.patterns = [(b'{', b'Success: Wifi attached$$$')]
        self.board.attach_wifi()

    def test_attach_wifi_failure(self):
        self.serial.patterns = [(b'{', b'Failure: Wifi not attached$$$')]
        with pytest.raises(RuntimeError):
            self.board.attach_wifi()

    def test_detach_wifi_success(self):
        self.serial.patterns = [(b'}', b'Success: Wifi removed$$$')]
        self.board._wifi_attached = True
        self.board.detach_wifi()

    def test_detach_wifi_failure(self):
        self.serial.patterns = [(b'}', b'Failure: Wifi not removed$$$')]
        self.board._wifi_attached = True
        with pytest.raises(RuntimeError):
            self.board.detach_wifi()

    def test_get_wifi_status_present(self):
        self.serial.patterns = [(b':', b'Wifi present$$$')]
        self.board._wifi_attached = True
        self.board.get_wifi_status()

    def test_get_wifi_status_not_present(self):
        self.serial.patterns = [
            (b':', b'Wifi not present, send { to attach the shield$$$')]
        self.board.get_wifi_status()

    def test_reset_wifi(self):
        self.serial.patterns = [(b';', b'Wifi soft reset$$$')]
        self.board.reset_wifi()

    ###########################################################################
    # Others
    def test_get_version(self):
        self.serial.patterns = [(b'V', b'v3.1.1$$$')]
        self.board.get_firmware_version()


class TestCytonReadSample(BaseCytonTestSuite):
    def test_read_sample_0xC0(self):
        """Test acquisition of standard sample with accel"""
        self.serial.patterns = [(
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
        self.board.start_streaming()
        sample = self.board.read_sample()

        assert sample.keys() == expected.keys()

        for key in sample:
            if key != 'timestamp':
                assert sample[key] == expected[key]
