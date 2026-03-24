"""pygame-compatible sndarray module."""

from __future__ import annotations

import io
import wave

import numpy as np

from ipygame.mixer import Sound

__all__ = [
    "array",
    "samples",
    "make_sound",
    "use_arraytype",
    "get_arraytype",
]


def _pcm_from_sound(sound) -> np.ndarray:
    """Extract PCM int16 samples from a Sound's raw WAV bytes."""
    raw = sound.get_raw()
    try:
        with wave.open(io.BytesIO(raw)) as wf:
            nchannels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            nframes = wf.getnframes()
            frames = wf.readframes(nframes)
    except Exception:
        raise ValueError("Sound does not contain valid WAV data")

    if sampwidth == 1:
        arr = np.frombuffer(frames, dtype=np.uint8)
    elif sampwidth == 2:
        arr = np.frombuffer(frames, dtype=np.int16)
    elif sampwidth == 4:
        arr = np.frombuffer(frames, dtype=np.int32)
    else:
        raise ValueError(f"Unsupported sample width: {sampwidth}")

    if nchannels > 1:
        arr = arr.reshape(-1, nchannels)
    return arr


def array(sound) -> np.ndarray:
    return _pcm_from_sound(sound).copy()


def samples(sound) -> np.ndarray:
    return _pcm_from_sound(sound)


def make_sound(array: np.ndarray) -> "Sound":
    from ipygame.mixer import Sound
    return Sound(array=array)


def use_arraytype(arraytype: str = "numpy") -> None:
    if arraytype.lower() != "numpy":
        raise ValueError("Only 'numpy' is supported")


def get_arraytype() -> str:
    return "numpy"
