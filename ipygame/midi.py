"""ipygame.midi stub module."""

from __future__ import annotations


def _not_implemented(*args, **kwargs):
    raise NotImplementedError("ipygame.midi is not supported in Jupyter notebooks")


def init():
    pass


def quit():
    pass


def get_init():
    return False


class Input:
    def __init__(self, *args, **kwargs):
        _not_implemented()


class Output:
    def __init__(self, *args, **kwargs):
        _not_implemented()


def get_count():
    return 0


def get_default_input_id():
    return -1


def get_default_output_id():
    return -1
