"""Helper module for generating channel config command and caching values."""


def get_channel_config_command(
        channel, power_down, gain, input_type, bias, srb2, srb1):
    """Get command string for the given parameters.

    See
    :func:`Cyton.configure_channel<openbci_interface.cyton.Cyton.configure_channel>`
    """
    command = [b'x']

    vals = {
        1: b'1', 9: b'Q',
        2: b'2', 10: b'W',
        3: b'3', 11: b'E',
        4: b'4', 12: b'R',
        5: b'5', 13: b'T',
        6: b'6', 14: b'Y',
        7: b'7', 15: b'U',
        8: b'8', 16: b'I',
    }
    if channel not in vals:
        raise ValueError('`channel` value must be one of %s' % vals.keys())
    command.append(vals[channel])

    vals = {
        0: b'0', 'ON': b'0',
        1: b'1', 'OFF': b'1',
    }
    if power_down not in vals:
        raise ValueError('`power_down` must be one of %s' % vals.keys())
    command.append(vals[power_down])

    vals = {
        1: b'0',
        2: b'1',
        4: b'2',
        6: b'3',
        8: b'4',
        12: b'5',
        24: b'6',
    }
    if gain not in vals:
        raise ValueError('`gain` value must be one of %s' % vals.keys())
    command.append(vals[gain])

    vals = {
        0: b'0', 'NORMAL': b'0',
        1: b'1', 'SHORTED': b'1',
        2: b'2', 'BIAS_MEAS': b'2',
        3: b'3', 'MVDD': b'3',
        4: b'4', 'TEMP': b'4',
        5: b'5', 'TESTSIG': b'5',
        6: b'6', 'BIAS_DRP': b'6',
        7: b'7', 'BIAS_DRN': b'7',
    }
    if input_type.upper() not in vals:
        raise ValueError(
            'When `input_type` type is str, '
            'value must be one of %s (case insensitive).' % vals.keys())
    command.append(vals[input_type])

    vals = {0: b'0', 1: b'1'}
    if bias not in vals.keys():
        raise ValueError('`bias` must be either 0 or 1.')
    command.append(vals[bias])

    vals = {0: b'0', 1: b'1'}
    if srb2 not in vals.keys():
        raise ValueError('`srb2` must be either 0 or 1.')
    command.append(vals[srb2])

    vals = {0: b'0', 1: b'1'}
    if srb1 not in vals.keys():
        raise ValueError('`srb1` must be either 0 or 1.')
    command.append(vals[srb1])

    command.append(b'X')
    return b''.join(command)


class ChannelConfig:
    """Class for holding channel configuration, set by Cyton.

    You should not use this class directly. Instead, you can use instances of
    this class managed by Cyton object, in read-only manner.

    Examples
    --------
    >>> cyton = openbci_interface.cyton.Cyton(port)
    >>> cyton.initialize()
    >>> print(cyton.channel_config[0].power_down)
    'ON'
    >>> cyton.configure_channel(1, power_down='OFF', ...)
    >>> print(cyton.channel_config[0].power_down)
    'OFF'

    :ivar bool enabled:
       If corresponding channel is enabled True, if disabled, False.
       None if not known. (initial value)

    :ivar str power_down:
       ``POWER_DOWN`` value. ``ON`` or ``OFF``

    :ivar int gain:
       ``GAIN_SET`` value. One of 1, 2, 4, 6, 8, 12, 24.

    :ivar str input_type:
       ``INPUT_TYPE_SET`` value. One of ``NORMAL``, ``SHORTED``, ``BIAS_MEAS``,
       ``MVDD``, ``TEMP``, ``TESTSIG``, ``BIAS_DRP``, or ``BIAS_DRN``.

    :ivar str bias:
       ``BIAS_SET`` value. 0 or 1.

    :ivar str srb2:
       ``SRB2_SET`` value. 0 or 1.

    :ivar str srb1:
       ``SRB1_SET`` value. 0 or 1.

    References
    ----------
    http://docs.openbci.com/OpenBCI%20Software/04-OpenBCI_Cyton_SDK#openbci-cyton-sdk-command-set-channel-setting-commands
    """
    def __init__(
            self, channel,
            enabled=None, power_down=None, gain=None,
            input_type=None, bias=None, srb2=None, srb1=None):
        self.channel = channel
        self.enabled = enabled
        self.power_down = power_down
        self.gain = gain
        self.input_type = input_type
        self.bias = bias
        self.srb2 = srb2
        self.srb1 = srb1

    def set_config(self, power_down, gain, input_type, bias, srb2, srb1):
        """Used by Cyton board to set values.

        See :func:`get_channel_config_command` for parameters.
        """
        # Assumption:
        # The provided argument values went through
        # `get_channel_config_command`, thus have valid values.

        # Normalize to str
        if isinstance(power_down, int):
            power_down = {0: 'ON', 1: 'OFF'}[power_down]
        if isinstance(input_type, int):
            input_type = {
                0: 'NORMAL',
                1: 'SHORTED',
                2: 'BIAS_MEAS',
                3: 'MVDD',
                4: 'TEMP',
                5: 'TESTSIG',
                6: 'BIAS_DRP',
                7: 'BIAS_DRN',
            }[input_type]

        self.power_down = power_down
        self.gain = gain
        self.input_type = input_type
        self.bias = bias
        self.srb2 = srb2
        self.srb1 = srb1

    def __repr__(self):
        return (
            'Channel: %d (%s), POWER_DOWN: %s, GAIN: %s, '
            'INPUT_TYPE: %s, BIAS_SET: %s, SRB2: %s, SRB1: %s'
        ) % (
            self.channel,
            'Enabled' if self.enabled else 'Disabled',
            self.power_down, self.gain, self.input_type,
            self.bias, self.srb2, self.srb1,
        )
