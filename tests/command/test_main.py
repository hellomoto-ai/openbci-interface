import pytest
import openbci_interface.__main__
import openbci_interface.command


def _main(_):
    pass


@pytest.mark.parametrize(
    'subcommand', openbci_interface.command.__all__,
)
def test_main(mocker, subcommand):
    """__main__ method works"""
    mocker.patch('openbci_interface.command.%s.main' % subcommand, _main)
    openbci_interface.__main__.main([subcommand, '--debug'])
