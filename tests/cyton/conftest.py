"""Define fixtures for testing cyton module"""
import logging

import pytest
from openbci_interface import cyton

from tests.serial_mock import SerialMock

_LG = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def cyton_mock():
    """Instanciate Cyton with SerialMock and inspect buffer at tear down"""
    serial = SerialMock()
    serial.open()
    yield cyton.Cyton(serial)
    serial.validate_no_message_in_buffer()
    serial.validate_all_patterns_consumed()
