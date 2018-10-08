"""Module for defining version number"""
import os

__all__ = ['__version__']


def _get_version(*path_components):
    with open(os.path.join(*path_components), 'r') as fileobj:
        return fileobj.read().strip()


__version__ = _get_version(os.path.dirname(__file__), 'VERSION')
