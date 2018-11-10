"""Implement Serial IO as defined in documentation"""
import struct
import logging

from openbci_interface import exception

_LG = logging.getLogger(__name__)


class Common:
    """Stateless interface common to Cyton and Ganglion

    Parameters
    ----------
    serial : Serial
    """
    def __init__(self, serial):
        self._serial = serial

    def read_message(self):
        """Read until ``$$$`` is found or timeout occurs.

        Returns
        -------
        bytes
            Message received from the board. If timeout occurs,
            the returned string might not end with ``$$$``.
        """
        return self._serial.read_until(b'$$$')

    def reset_board(self):
        """Reset the board state.

        References
        ----------
        http://docs.openbci.com/Hardware/03-Cyton_Data_Format#cyton-data-format-startup
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-miscellaneous
        http://docs.openbci.com/OpenBCI%20Software/06-OpenBCI_Ganglion_SDK#openbci-ganglion-sdk-command-set-miscellaneous
        """
        self._serial.write(b'v')

    def query_sample_rate(self):
        """Query the current sample rate. Message must be read separately.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-sample-rate
        http://docs.openbci.com/OpenBCI%20Software/06-OpenBCI_Ganglion_SDK#openbci-ganglion-sdk-firmware-v2xx-new-commands-sample-rate
        """
        self._serial.write(b'~~')

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
        sample_rate : bytes
            One of ``b'7'``, ``b'6'``, ``b'5'``, ``b'4'``,
            ``b'3'``, ``b'2'``, ``b'1'``, or ``b'0'``.


        .. note::
           Only Ganglion supports ``b'7'`` (200 Hz).

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-sample-rate
        http://docs.openbci.com/OpenBCI%20Software/06-OpenBCI_Ganglion_SDK#openbci-ganglion-sdk-firmware-v2xx-new-commands-sample-rate
        """
        vals = [b'6', b'5', b'4', b'3', b'2', b'1', b'0']
        if sample_rate not in vals:
            raise ValueError('Sample rate must be one of %s' % vals)
        self._serial.write(b'~' + sample_rate)

    def attach_wifi(self):
        """Attach WiFi shield.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-wifi-shield-commands
        http://docs.openbci.com/OpenBCI%20Software/06-OpenBCI_Ganglion_SDK#openbci-ganglion-sdk-firmware-v2xx-new-commands-wifi-shield-commands
        """
        self._serial.write(b'{')

    def detach_wifi(self):
        """Detach WiFi shield.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-wifi-shield-commands
        http://docs.openbci.com/OpenBCI%20Software/06-OpenBCI_Ganglion_SDK#openbci-ganglion-sdk-firmware-v2xx-new-commands-wifi-shield-commands
        """
        self._serial.write(b'}')

    def query_wifi_status(self):
        """Query the status of WiFi shield. Message must be read separately.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-wifi-shield-commands
        http://docs.openbci.com/OpenBCI%20Software/06-OpenBCI_Ganglion_SDK#openbci-ganglion-sdk-firmware-v2xx-new-commands-wifi-shield-commands
        """
        self._serial.write(b':')

    def reset_wifi(self):
        """Perform a soft (power) reset of the WiFi shield.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-wifi-shield-commands
        http://docs.openbci.com/OpenBCI%20Software/06-OpenBCI_Ganglion_SDK#openbci-ganglion-sdk-firmware-v2xx-new-commands-wifi-shield-commands
        """
        self._serial.write(b';')

    def enable_channel(self, channel):
        """Turn on channel for sample acquisition

        Parameters
        ----------
        channel : bytes
            One of ``!@#$%^&*QWERTYUI``.


        .. note::
           Ganglion supports (the first) 4 channels, Cyton supports 8 channels,
           Cyton with Daisy module supports 16 channels.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-16-channel-commands-turn-channels-on
        http://docs.openbci.com/OpenBCI%20Software/06-OpenBCI_Ganglion_SDK#openbci-ganglion-sdk-command-set-turn-channels-on
        """
        vals = [
            b'!', b'@', b'#', b'$', b'%', b'^', b'&', b'*',
            b'Q', b'W', b'E', b'R', b'T', b'Y', b'U', b'I',
        ]
        if channel not in vals:
            raise ValueError('`channel` value must be one of %s' % vals)
        self._serial.write(channel)

    def disable_channel(self, channel):
        """Turn off channel for sample acquisition

        Parameters
        ----------
        channel : bytes
            One of ``12345678qwertyui``


        .. note::
           Ganglion supports (the first) 4 channels, Cyton supports 8 channels,
           Cyton with Daisy module supports 16 channels.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-16-channel-commands-turn-channels-off
        http://docs.openbci.com/OpenBCI%20Software/06-OpenBCI_Ganglion_SDK#openbci-ganglion-sdk-command-set-turn-channels-off
        """
        command = [
            b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8',
            b'q', b'w', b'e', b'r', b't', b'y', b'u', b'i',
        ]
        if channel not in command:
            raise ValueError('`channel` value must be one of %s' % command)
        self._serial.write(channel)

    def start_streaming(self):
        """Start streaming data.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-stream-data-commands
        http://docs.openbci.com/OpenBCI%20Software/06-OpenBCI_Ganglion_SDK#openbci-ganglion-sdk-command-set-stream-data-commands
        """
        self._serial.write(b'b')

    def stop_streaming(self):
        """Stop streaming data.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-stream-data-commands
        http://docs.openbci.com/OpenBCI%20Software/06-OpenBCI_Ganglion_SDK#openbci-ganglion-sdk-command-set-stream-data-commands
        """
        self._serial.write(b's')


class CytonBoard(Common):
    """Stateless interface to Cyton"""

    START_BYTE = 0xA0

    def query_firmware_version(self):
        """Query firmware version. Message must be read separately.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-get-version
        """
        self._serial.write(b'V')

    def query_board_mode(self):
        """Query the current board mode. Message must be read separately.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-board-mode
        """
        self._serial.write(b'//')

    def set_board_mode(self, mode):
        """Set board mode.

        Parameters
        ----------
        mode : bytes
            ``b'0'``, ``b'1'``, ``b'2'``, ``b'3'`` or ``b'4'``

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v300-new-commands-board-mode
        """
        vals = [b'0', b'1', b'2', b'3', b'4']
        if mode not in vals:
            raise ValueError('Board mode must be one of %s' % vals)
        self._serial.write(b'/' + mode)

    def attach_daisy(self):
        """Set the number of maximum chnnels to 16.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-16-channel-commands-select-maximum-channel-number
        """
        self._serial.write(b'C')

    def detach_daisy(self):
        """Set the number of maximum channels to 8

        .. note::
           On reset, the OpenBCI Cyton board will sniff for the Daisy Module,
           and if it is present, it will default to 16 channel capability.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-16-channel-commands-select-maximum-channel-number
        """
        self._serial.write(b'c')

    def configure_channel(self, command):
        """Configure channel.

        Parameters
        ----------
        command : bytes
            9-length byte string in the following format.
            ``x (CHANNEL, POWER_DOWN, GAIN_SET,
            INPUT_TYPE_SET, BIAS_SET, SRB2_SET, SRB1_SET) X``.
            See the reference for the detail.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-channel-setting-commands
        """
        self._serial.write(command)

    def enable_timestamp(self):
        """Enable timestamp

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v200-new-commands-time-stamping
        """
        self._serial.write(b'<')

    def disable_timestamp(self):
        """Disable timestamp

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-firmware-v200-new-commands-time-stamping
        """
        _LG.info('Disabling timestamp.')
        self._serial.write(b'>')

    def reset_channels(self):
        """Set all channels to default configuration.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-default-channel-settings
        """
        self._serial.write(b'd')

    def query_default_settings(self):
        """Query channel default configs. Message must be read separately.

        References
        ----------
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-default-channel-settings
        http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-channel-setting-commands
        """
        self._serial.write(b'D')

    def wait_start_byte(self):
        """Keep reading data until start byte is found.

        References
        ----------
        http://docs.openbci.com/Hardware/03-Cyton_Data_Format#cyton-data-format-binary-format
        """
        n_skipped = 0
        while True:
            val = self._serial.read()
            if not val:
                raise exception.SampleAcquisitionTimeout(
                    'Time out occurred while waiting for a start byte.')
            if struct.unpack('B', val)[0] == self.START_BYTE:
                break
            n_skipped += 1
        if n_skipped:
            _LG.warning('Skipped %d bytes at start.', n_skipped)

    def read_packet(self):
        """Read 32 byte packet.

        References
        ----------
        http://docs.openbci.com/Hardware/03-Cyton_Data_Format#cyton-data-format-binary-format
        """
        packet_id = self._read_packet_id()
        raw_eeg = self._read_eeg_data()
        raw_aux = self._read_aux_data()
        stop_byte = self._read_stop_byte()
        return {
            'packet_id': packet_id,
            'eeg': raw_eeg,
            'aux': raw_aux,
            'stop_byte': stop_byte,
        }

    def _read_packet_id(self):
        return struct.unpack('B', self._serial.read())[0]

    def _read_eeg_data(self):
        return [self._serial.read(3) for _ in range(8)]

    def _read_aux_data(self):
        return [self._serial.read(2) for _ in range(3)]

    def _read_stop_byte(self):
        return struct.unpack('B', self._serial.read())[0]
