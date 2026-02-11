from __future__ import annotations


def _not_implemented(*args, **kwargs):
    raise NotImplementedError("ipygame.camera is not supported in Jupyter notebooks")


colorspace = _not_implemented
list_cameras = _not_implemented


class Camera:
    def __init__(self, *args, **kwargs):
        _not_implemented()
