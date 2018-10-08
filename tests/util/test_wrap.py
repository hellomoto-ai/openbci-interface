import pytest
from openbci_interface import util, cyton

from . import conftest

pytestmark = [pytest.mark.util, pytest.mark.util_wrap]


@pytest.mark.parametrize('port', [
    'cyton_8bit', 'cyton_v1', 'cyton_v2', 'cyton_v3',
])
def test_cyton_detection(port):
    serial_obj = conftest.SerialMock(port=port)
    assert isinstance(util.wrap(serial_obj), cyton.Cyton)


@pytest.mark.parametrize('port', ['ganglion_v2'])
def test_ganglion_detection(port):
    serial_obj = conftest.SerialMock(port=port)
    with pytest.raises(NotImplementedError):
        util.wrap(serial_obj)


@pytest.mark.parametrize('port', ['foo', 'bar'])
def test_non_openbci_board(port):
    serial_obj = conftest.SerialMock(port=port)
    with pytest.raises(RuntimeError):
        util.wrap(serial_obj)
