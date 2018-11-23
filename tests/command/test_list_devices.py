from openbci_interface.command import list_devices


def _lists(filter_regex=None):
    return ['foo', 'bar']


def test_list_devices(mocker):
    """Test ``list_devices`` command"""
    mocker.patch(
        'openbci_interface.command.list_devices.util.list_devices', _lists)
    list_devices.main([])
