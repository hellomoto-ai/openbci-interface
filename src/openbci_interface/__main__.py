"""Entrypoint for CLI"""

import logging
import argparse

from openbci_interface import __version__
import openbci_interface.command


VERSION_STRING = 'OpenBCI Interface {}'.format(__version__)


def _parse_args(commands):
    parser = argparse.ArgumentParser(
        description='Interact with OpenBCI boards.',
        add_help=False,
    )
    parser.add_argument('command', choices=commands)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--version', action='version', version=VERSION_STRING)
    namespace, args = parser.parse_known_args()

    if namespace.debug:
        # it's often useful to be able to access debug flag in sub command
        args.append('--debug')
    return namespace, args


def main():
    """Entrypoint for `openbci_interface` command"""
    subcommands = {
        module: getattr(openbci_interface.command, module)
        for module in openbci_interface.command.__all__
    }
    namespace, args = _parse_args(subcommands.keys())
    _init_logger(namespace.debug)
    subcommands[namespace.command](args)


def _init_logger(debug=False):
    """Initialize logger"""
    header = '%(asctime)s: %(levelname)5s'
    if debug:
        header += ' %(funcName)10s %(lineno)d'
    format_ = '{}: %(message)s'.format(header)
    logging.basicConfig(
        format=format_,
        level=logging.DEBUG if debug else logging.INFO,
    )


if __name__ == '__main__':
    main()
