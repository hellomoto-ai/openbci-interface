"""Define interface to Cyton board"""
import re
import time
import struct
import logging
import warnings

from openbci_interface.core import CytonBoard
from openbci_interface import util, channel_config

_LG = logging.getLogger(__name__)

STOP_BYTE = 0xC0

ADS1299VREF = 4.5
AUX_SCALE = 0.002 / pow(2, 4)


def _parse_sample_rate(message):
    pattern = r'.*\s(\d+)\s*Hz\$\$\$'
    matched = re.match(pattern, message)
    ret = None
    if matched:
        ret = int(matched.group(1))
    else:
        _LG.warning('Failed to parse sample rate; %s', message)
    return ret


def _parse_board_mode(message):
    pattern = r'.*\s(\S+)\$\$\$'
    matched = re.match(pattern, message)
    ret = None
    if matched:
        ret = matched.group(1)
    else:
        _LG.warning('Failed to parse board mode; %s', message)
    return ret


def _unpack_24bit_signed_int(raw):
    prefix = b'\xFF' if struct.unpack('3B', raw)[0] & 0x80 > 0 else b'\x00'
    return struct.unpack('>i', prefix + raw)[0]


def _unpack_16bit_signed_int(raw):
    prefix = b'\xFF' if struct.unpack('2B', raw)[0] & 0x80 > 0 else b'\x00'
    return struct.unpack('>i', prefix * 2 + raw)[0]


def _parse_aux(stop_byte, raw_data):
    if stop_byte != 0xC0:
        warnings.warn(
            'Stop Byte is %s. Formats other than 0xC0 '
            '(Standard with accel) is not implemented.' % stop_byte)
    return [AUX_SCALE * _unpack_16bit_signed_int(v) for v in raw_data]


def _get_eeg_scale(gain):
    return 1000000. * ADS1299VREF / gain / (pow(2, 23) - 1)


def _parse_eeg(raw_eeg, gain=None):
    if gain is None:
        warnings.warn('Gain value is not explicitly set. Using 24.')
        gain = 24
    scale = _get_eeg_scale(gain)
    return _unpack_24bit_signed_int(raw_eeg) * scale


class Cyton:
    """Interface to Cyton board.

    Parameters
    ----------
    serial : serial.Serial, str or dict
        Serial object used to communicate with board.
        If str object is passed, it is interpreted as port and a
        new Serial object is constructed.
        If dict object is passed, it is passed to constructor of
        serial.Serial class as keyword arguments.

    close_on_finalize : bool
        If True, underlying serial connection is closed when
        :func:`finalize` is called.


    :cvar int num_aux: The number of AUX channels. (3)

    :ivar str board_info:
       The message returned by Cyton board when resetting the board.
       This variable is set when :func:`reset_board` method is called.

    :ivar str firmware_version:
       Firmware version string.
       This variable is set when :func:`get_firmware_version` method is called.

    :ivar str board_mode:
       Board mode string.
       This variable is set when either :func:`get_board_mode` or
       :func:`set_board_mode` is called.

    :ivar int sample_rate:
       Sampling rate.
       This variable is set when either :func:`get_sample_rate` or
       :func:`set_sample_rate` is called.

    :ivar bool streaming:
       True if streaming

    :ivar bool wifi_attached:
       True if WiFi is attached via :func:`attach_wifi` method.

    :ivar list channel_configs:
       List of
       :class:`ChannelConfig<openbci_interface.channel_config.ChannelConfig>`.
       For Daisy compatibility, this list always has 16 items.
       Use :func:`num_eeg` to get the number of valid channels.

    :ivar bool daisy_attached:
       True if Daisy module is detected in :func:`reset_board`,
       otherwise False.

    References
    ----------
    http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK
    http://docs.openbci.com/Hardware/03-Cyton_Data_Format

    .. automethod:: __enter__

    .. automethod:: __exit__
    """

    num_aux = 3  # The number of AUX channels.

    def __init__(self, serial, close_on_finalize=True):
        if isinstance(serial, str):
            serial = serial.Serial(port=serial, baudrate=115200, timeout=2)
        elif isinstance(serial, dict):
            serial = serial.Serial(**serial)
        self._serial = serial
        self._board = CytonBoard(self._serial)
        self._close_on_finalize = close_on_finalize

        # Public (read-only) attributes
        # Since a serial communication must happen to alter the state of
        # board, and these are implemented in method with explicit names,
        # we use attributes without under score prefix for read-only
        # property. User should not alter these properties.
        self.board_info = None
        self.firmware_version = None
        self.board_mode = None
        self.sample_rate = None
        self.streaming = False
        self.wifi_attached = False
        self.channel_configs = [
            channel_config.ChannelConfig(i) for i in range(16)]
        self.daisy_attached = False

    @property
    def num_eeg(self):
        """The number of EEG channels. 16 if Daisy is attached, otherwise 8"""
        return 16 if self.daisy_attached else 8

    def read_message(self):
        """Read until ``$$$`` is found or timeout occurs.

        Returns
        -------
        str
            Message received from the board.

        Raises
        ------
        :class:`UnexpectedMessageFormat<openbci_interface.exception.UnexpectedMessageFormat>`
            The message received from the board does not end with ``$$$``
            (which is likely due to timeout).

        :class:`DeviceNotConnected<openbci_interface.exception.DeviceNotConnected>`
            Serial connection is working, but no board is avaialable.
        """
        msg = self._board.read_message()
        _LG.debug('    %s', msg)
        msg = msg.decode('utf-8', errors='ignore')
        util.validate_message(msg)
        for line in msg.split('\n'):
            _LG.info('   %s', line)
        return msg

    def reset_board(self):
        """Reset the board state.

        References
        ----------
        http://docs.openbci.com/Hardware/03-Cyton_Data_Format#cyton-data-format-startup
        """
        _LG.info('Resetting board...')
        self._board.reset_board()
        self.board_info = self.read_message()
        self.daisy_attached = 'Daisy' in self.board_info

    def get_firmware_version(self):
        """Get firmware version

        Returns
        -------
        str
            Version string

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-get-version
        """
        _LG.info('Getting firmware version')
        self._board.query_firmware_version()
        self.firmware_version = self.read_message().replace('$$$', '')
        return self.firmware_version

    def get_board_mode(self):
        """Get the current board mode.

        Returns
        -------
        str or None
            One of ``default``, ``debug``, ``analog``, ``digital``, ``marker``
            if the mode string is parsed successfully. Otherwise None.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-board-mode
        """
        _LG.info('Getting board mode...')
        self._board.query_board_mode()
        self.board_mode = _parse_board_mode(self.read_message())
        return self.board_mode

    def set_board_mode(self, mode):
        """Set board mode.

        Parameters
        ----------
        mode : str
            ``default``, ``debug``, ``analog``, ``digital`` or ``marker``

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-board-mode
        """
        _LG.info('Setting board mode: %s', mode)
        mode = mode.lower()
        vals = {
            'default': b'0',
            'debug': b'1',
            'analog': b'2',
            'digital': b'3',
            'marker': b'4',
        }
        if mode not in vals:
            raise ValueError('Board mode must be one of %s' % vals.keys())
        self._board.set_board_mode(vals[mode])
        self.board_mode = _parse_board_mode(self.read_message())

    def attach_daisy(self):
        """Attach Daisy.

        After successful attach, ``daisy_attached`` is set to True.

        .. note::
           On reset, the OpenBCI Cyton board will default to 16 channel if
           Daisy module is present.
           So this method is only useful for re-attaching Daisy.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-16-channel-commands-select-maximum-channel-number
        """
        if self.daisy_attached:
            _LG.warning('Daisy already attached.')
            return
        self._board.attach_daisy()
        message = self.read_message()
        pattern = r'[\D]*(\d{1,2})\$\$\$'
        n_channels = int(re.search(pattern, message).group(1))
        self.daisy_attached = n_channels == 16

    def detach_daisy(self):
        """Detach Daisy.

        After this method is called, ``daisy_attached`` is set to False.

        .. note::
           On reset, the OpenBCI Cyton board will sniff for the Daisy Module,
           and if it is present, it will default to 16 channel capability.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-16-channel-commands-select-maximum-channel-number
        """
        if not self.daisy_attached:
            _LG.warning('Daisy not attached.')
            return
        self._board.detach_daisy()
        self.read_message()
        self.daisy_attached = False

    def get_sample_rate(self):
        """Get the current sample rate.

        Returns
        -------
        int or None
            Sample rate on successful parse, else None.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-sample-rate
        """
        _LG.info('Getting sample rate...')
        self._board.query_sample_rate()
        message = self.read_message()
        self.sample_rate = _parse_sample_rate(message)
        return self.sample_rate

    def set_sample_rate(self, sample_rate):
        """Set the sample rate.

        .. note::
           The Cyton with USB Dongle cannot and will not stream data over
           250SPS.
           Plug in the WiFi Shield to get speeds over 250SPS streaming.
           You may still write to an SD card though, the firmware will not
           send EEG data over the Bluetooth radios.

        Parameters
        ----------
        sample_rate : int
            One of ``250``, ``500``, ``1000``, ``2000``,
            ``4000``, ``8000`` or ``1600``.

        Returns
        -------
        int or None
            Sample rate on successful parse, else None.

        Raises
        ------
        ValueError
            When the provided ``sample_rate`` is invalid.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-sample-rate
        """
        _LG.info('Setting sample rate: %s', sample_rate)
        vals = {
            250: b'6', 500: b'5', 1000: b'4',
            2000: b'3', 4000: b'2', 8000: b'1', 16000: b'0',
        }
        if sample_rate not in vals:
            raise ValueError('Sample rate must be one of %s' % vals.keys())
        self._board.set_sample_rate(vals[sample_rate])
        message = self.read_message()
        self.sample_rate = _parse_sample_rate(message)
        return self.sample_rate

    def attach_wifi(self):
        """Attach WiFi shield.

        After successful attachment, ``wifi_attached`` is set to True.

        Raises
        ------
        RuntimeError
            When failed to attach WiFi shield.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-wifi-shield-commands
        """
        if self.wifi_attached:
            _LG.warning('WiFi shield already attached.')
            return
        _LG.info('Attaching WiFi shield...')
        self._board.attach_wifi()
        message = self.read_message()
        if 'failure' in message.lower():
            raise RuntimeError(message)
        self.wifi_attached = True

    def detach_wifi(self):
        """Detach WiFi shield.

        After successful detachment, ``wifi_attached`` is set to False.

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            When failed to detach Wifi shield.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-wifi-shield-commands
        """
        if not self.wifi_attached:
            _LG.warning('No WiFi shield to detach.')
            return
        _LG.info('Detaching WiFi shield...')
        self._board.detach_wifi()
        message = self.read_message()
        if 'failure' in message.lower():
            raise RuntimeError(message)
        self.wifi_attached = False

    def get_wifi_status(self):
        """Get the status of WiFi shield.

        ``wifi_attached`` is updated based on the result.

        Returns
        -------
        str
            Message received from the board.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-wifi-shield-commands
        """
        _LG.info('Getting WiFi shield status.')
        self._board.query_wifi_status()
        message = self.read_message()
        self.wifi_attached = 'not present' not in message
        return message

    def reset_wifi(self):
        """Perform a soft (power) reset of the WiFi shield.

        Returns
        -------
        str
            Message received from the board.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-wifi-shield-commands
        """
        self._board.reset_wifi()
        _LG.info('Resetting WiFi shield.')
        return self.read_message()

    def enable_channel(self, channel):
        """Turn on channel for sample acquisition

        Parameters
        ----------
        channel : int
            value must be between 1 - 16, inclusive.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-16-channel-commands-turn-channels-on
        """
        command = {
            1: b'!', 2: b'@', 3: b'#', 4: b'$',
            5: b'%', 6: b'^', 7: b'&', 8: b'*',
            9: b'Q', 10: b'W', 11: b'E', 12: b'R',
            13: b'T', 14: b'Y', 15: b'U', 16: b'I',
        }
        if channel not in command:
            raise ValueError('`channel` value must be in range of [1, 8]')
        _LG.info('Enabling channel: %s', channel)
        self._board.enable_channel(command[channel])
        self.channel_configs[channel-1].enabled = True

    def disable_channel(self, channel):
        """Turn off channel for sample acquisition

        Parameters
        ----------
        channel : int
            value must be between 1 - 8, inclusive.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-16-channel-commands-turn-channels-off
        """
        command = {
            1: b'1', 2: b'2', 3: b'3', 4: b'4',
            5: b'5', 6: b'6', 7: b'7', 8: b'8',
            9: b'q', 10: b'w', 11: b'e', 12: b'r',
            13: b't', 14: b'y', 15: b'u', 16: b'i',
        }
        if channel not in command:
            raise ValueError('`channel` value must be in range of [1, 8]')
        _LG.info('Disabling channel: %s', channel)
        self._board.disable_channel(command[channel])
        self.channel_configs[channel-1].enabled = False

    def configure_channel(
            self, channel,
            power_down='ON', gain=24,
            input_type='NORMAL', bias=1, srb2=1, srb1=0):
        """Configure channel.

        Parameters
        ----------
        channel : int
            Channel to configure. [1, 8] for Cyton, [1, 16] for Daisy.

        power_down : str or int
            ``POWER_DOWN`` value. ``ON`` or ``OFF`` if string.
            0 (==ON) or 1 (==OFF) if integer.

        gain : int
            ``GAIN_SET`` value. One of 1, 2, 4, 6, 8, 12, 24.

        input_type : str or int
            ``INPUT_TYPE_SET`` value. One of ``NORMAL`` (corresponding integer
            value: 0), ``SHORTED`` (1), ``BIAS_MEAS`` (2), ``MVDD`` (3),
            ``TEMP`` (4), ``TESTSIG`` (5), ``BIAS_DRP`` (6), or
            ``BIAS_DRN`` (7).

        bias : int
            ``BIAS_SET`` value. 0 for remove, 1 for include.

        srb2 : int
            ``SRB2_SET`` value. 0 for disconnect, 1 for connect.

        srb1 : int
            ``SRB1_SET`` value. 0 for disconnect, 1 for connect.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-channel-setting-commands
        """
        command = channel_config.get_channel_config_command(
            channel=channel, power_down=power_down, gain=gain,
            input_type=input_type, bias=bias, srb2=srb2, srb1=srb1,
        )
        _LG.info('Configuring channel: %s', channel)
        self._board.configure_channel(command)
        self.channel_configs[channel-1].set_config(
            power_down=power_down, gain=gain,
            input_type=input_type, bias=bias, srb2=srb2, srb1=srb1,
        )
        if not self.streaming or self.wifi_attached:
            message = self.read_message()
            if 'failure' in message.lower():
                raise RuntimeError(message)

    def start_streaming(self):
        """Start streaming data.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-stream-data-commands
        """
        _LG.info('Start streaming.')
        self._board.start_streaming()
        self.streaming = True
        if self.wifi_attached:
            self.read_message()

    def stop_streaming(self):
        """Stop streaming data.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-stream-data-commands
        """
        _LG.info('Stop streaming.')
        self._board.stop_streaming()
        self.streaming = False
        if self.wifi_attached:
            self.read_message()

    def enable_timestamp(self):
        """Enable timestamp

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v200-new-commands-time-stamping

        .. note::
           Timestamp parsing is not supported yet.

        .. todo::
           Implement timestamp parsing.

        """
        _LG.info('Enabling timestamp.')
        self._board.enable_timestamp()
        if not self.streaming:
            self.read_message()

    def disable_timestamp(self):
        """Disable timestamp

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v200-new-commands-time-stamping
        """
        _LG.info('Disabling timestamp.')
        self._board.disable_timestamp()
        if not self.streaming:
            self.read_message()

    def reset_channels(self):
        """Set all channels to default configuration.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-default-channel-settings
        """
        _LG.info('Setting all channels to default.')
        self._board.reset_channels()
        self.read_message()

    def get_default_settings(self):
        """Get channel default configuration string.

        Returns
        -------
        dict
            Parameters compatible with :func:`configure_channel` method.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-default-channel-settings
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-channel-setting-commands
        """
        _LG.info('Getting default channel settings.')
        self._board.query_default_settings()
        val = self.read_message().replace('$$$', '')

        power_down = {'0': 'ON', '1': 'OFF'}[val[0]]
        gain = {
            '0': 1, '1': 2, '2': 4, '3': 6,
            '4': 8, '5': 12, '6': 24}[val[1]]
        input_type = {
            '0': 'NORMAL', '1': 'SHORTED',
            '2': 'BIAS_MEAS', '3': 'MVDD',
            '4': 'TEMP', '5': 'TESTSIG',
            '6': 'BIAS_DRP', '7': 'BIAS_DRN',
        }[val[2]]
        bias = {'0': 0, '1': 1}[val[3]]
        srb2 = {'0': 0, '1': 1}[val[4]]
        srb1 = {'0': 0, '1': 1}[val[5]]

        return {
            'power_down': power_down,
            'gain': gain,
            'input_type': input_type,
            'bias': bias,
            'srb2': srb2,
            'srb1': srb1,
        }

    def __enter__(self):
        """Context manager for open/close serial connection automatically.

        By utilizing context manager with ``with`` statement, board is
        initialized automatically after serial connection is established.
        Streaming is stopped and serial connection is closed automatically
        at exit.

        .. code-block:: python

           with Cyton(port, baudrate, timeout) as board:
               # no need to call board.initialize()
               board.start_streaming()
               board.read_sample()
               # no need to call board.stop_streaming()

        However when passing an already-opened Serial instance to
        :func:`Cyton<openbci_interface.cyton.Cyton>`, context manager
        does not close the serial.

        .. code-block:: python

           # Passing an instance with open connection
           ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
           with Cyton(ser) as board:
               pass
           assert ser.is_open  # Connection is still open.

        .. code-block:: python

           # Passing an instance with connection not opened yet.
           ser = serial.Serial(baudrate=baudrate, timeout=timeout)
           ser.port = port
           with Cyton(ser) as board:
               pass
           assert not ser.is_open  # Connection is closed.
        """
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager for open/close serial connection automatically.

        See :func:`__enter__<openbci_interface.cyton.Cyton.__enter__>`
        """
        self.finalize()
        return exc_type in [None, KeyboardInterrupt]

    def read_sample(self):
        """Read one sample from channels.

        Returns
        -------
        dict

            .. code-block:: javascript

               {
                 'eeg': [<channel1>, ..., <channelN>],
                 'aux': [<channel1>, ..., <channel3>],
                 'packet_id': int,
                 'timestamp': float,
               }


        .. note::
            This method will discard the message received from board
            before receiving start byte.

        .. note::
           The output format is subject to change.

        .. note::
           For AUX data, only ``0xC0`` stop byte is supported now.


        Raises
        ------
        openbci_interface.exception.SampleAcquisitionTimeout
            If time out occurs while waiting for a start byte.

        References
        ----------
        http://docs.openbci.com/Hardware/03-Cyton_Data_Format#cyton-data-format-binary-format
        """
        sample = self._read_packet()
        if self.daisy_attached:
            sample['eeg'].extend(self._read_packet()['eeg'])
        sample['timestamp'] = time.time()
        return sample

    def _read_packet(self):
        self._board.wait_start_byte()
        data = self._board.read_packet()
        data['eeg'] = self._parse_eeg(data['eeg'])
        data['aux'] = _parse_aux(data['stop_byte'], data['aux'])
        return {key: data[key] for key in ['packet_id', 'eeg', 'aux']}

    def _parse_eeg(self, raw_eeg_data):
        return [
            _parse_eeg(raw_eeg, self.channel_configs[i].gain)
            for i, raw_eeg in enumerate(raw_eeg_data)
        ]

    ###########################################################################
    # Higher level function
    def initialize(self, board_mode='default', sample_rate=250):
        """Initialize connection, board then configure channel to default.

        Returns
        -------
        str
            Message received when issueing :func:`reset` method.
        """
        wait_time = 0.1  # value picked up randomly without logical meaning
        self.reset_board()
        self.get_firmware_version()
        self.set_board_mode(board_mode)
        self.set_sample_rate(sample_rate)
        conf = self.get_default_settings()
        for i in range(self.num_eeg):
            # Channel configuration commands are non-blocking
            # so adding some wait time here.
            self.enable_channel(i + 1)
            time.sleep(wait_time)
            self.configure_channel(i + 1, **conf)
            time.sleep(wait_time)

    def finalize(self):
        """Stop streaming if necessary then close connection"""
        if self.streaming:
            self.stop_streaming()
        if self._close_on_finalize:
            self._serial.close()
