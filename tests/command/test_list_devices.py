from openbci_interface import command


def test_list_devices():
    command.list_devices([])
