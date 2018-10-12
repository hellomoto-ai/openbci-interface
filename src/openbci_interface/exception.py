"""Defines exceptions commonly used in open_bci module."""


class BCIException:
    """Base exception for OpenBCI Interface specific exception."""
    pass


class UnexpectedMessageFormat(BCIException, ValueError):
    """Board returned message not in OpenBCI format"""
    def __init__(self, message):
        super().__init__(
            'Device returned a message not in OpenBCI format; %s' % message)


class NotSupported(BCIException, NotImplementedError):
    """Unsupported board type was requested"""
    def __init__(self, board_type):
        super().__init__('Unsupported device; %s.' % board_type)


class DeviceNotConnected(BCIException, RuntimeError):
    """Serial is working but board is not connected"""
    pass
