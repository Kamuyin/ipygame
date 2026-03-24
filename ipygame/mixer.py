"""pygame-compatible mixer module backed by IPython HTML5 <audio> elements.

Sound playback is performed through the browser's native audio engine.
Each :class:`Sound` object holds its audio data as a data-URI.  Calling
:meth:`Sound.play` (or :meth:`Channel.play`) injects an ``<audio>`` tag
into the notebook output and controls it via tiny JS snippets. (I'm quite proud of this ᕙ(`▽´)ᕗ)
"""

from __future__ import annotations

import base64
import io
import uuid
import wave
from pathlib import Path
from typing import BinaryIO, Union

import numpy as np

from ipygame import constants as _c

__all__ = [
    "init",
    "pre_init",
    "quit",
    "get_init",
    "get_num_channels",
    "set_num_channels",
    "set_reserved",
    "find_channel",
    "get_busy",
    "stop",
    "pause",
    "unpause",
    "fadeout",
    "Sound",
    "Channel",
    "get_sdl_mixer_version",
    "get_driver",
    "set_soundfont",
    "get_soundfont",
    "music",
]

FileLike = Union[str, Path, BinaryIO]

# Mod state

_initialized: bool = False
_frequency: int = 44100
_size: int = -16
_channels_count: int = 2
_buffer: int = 512
_num_channels: int = 8
_reserved: int = 0
_soundfont: str | None = None

_channel_pool: dict[int, "Channel"] = {}


def _get_ipython_display():
    try:
        from IPython.display import display as ipy_display, HTML
        return ipy_display, HTML
    except ImportError:
        return None, None


def _run_js(snippet: str) -> None:
    # Helper to run a JS snippet in the notebook output.
    ipy_display, HTML = _get_ipython_display()
    if ipy_display is None:
        return
    ipy_display(HTML(f"<script>{snippet}</script>"))


# WAV encoding helpers

def _array_to_wav_bytes(
    arr: np.ndarray,
    rate: int = 44100,
) -> bytes:
    """Encode a NumPy array as a WAV byte string.

    *arr* can be 1-D (mono) or 2-D with shape ``(nframes, nchannels)``.
    """
    if arr.ndim == 1:
        nchannels = 1
        frames = arr
    elif arr.ndim == 2:
        nchannels = arr.shape[1]
        frames = arr
    else:
        raise ValueError("array must be 1-D or 2-D")

    if frames.dtype in (np.float32, np.float64):
        frames = np.clip(frames, -1.0, 1.0)
        frames = (frames * 32767).astype(np.int16)
    elif frames.dtype == np.uint8:
        pass
    else:
        frames = frames.astype(np.int16)

    sampwidth = 2 if frames.dtype != np.uint8 else 1

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(nchannels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(rate)
        wf.writeframes(frames.tobytes())
    return buf.getvalue()


def _file_to_data_uri(file: FileLike) -> str:
    """Read *file* and return a ``data:audio/…;base64,…`` URI."""
    if isinstance(file, (str, Path)):
        p = Path(file)
        raw = p.read_bytes()
        ext = p.suffix.lower()
    else:
        raw = file.read()
        ext = ""

    mime_map = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
    }
    mime = mime_map.get(ext, "audio/wav")
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"



def init(
    frequency: int = 44100,
    size: int = -16,
    channels: int = 2,
    buffer: int = 512,
    devicename: str | None = None,
    allowedchanges: int = 5,
) -> None:
    """Initialize the mixer."""
    global _initialized, _frequency, _size, _channels_count, _buffer
    _frequency = frequency
    _size = size
    _channels_count = channels
    _buffer = buffer
    _initialized = True


def pre_init(
    frequency: int = 44100,
    size: int = -16,
    channels: int = 2,
    buffer: int = 512,
    devicename: str | None = None,
    allowedchanges: int = 5,
) -> None:
    """Pre-set mixer parameters (applied on next :func:`init`)."""
    global _frequency, _size, _channels_count, _buffer
    _frequency = frequency
    _size = size
    _channels_count = channels
    _buffer = buffer


def quit() -> None:
    """Uninitialize the mixer."""
    global _initialized
    stop()
    _initialized = False
    _channel_pool.clear()


def get_init() -> tuple[int, int, int] | None:
    """Return ``(frequency, size, channels)`` or ``None``."""
    if not _initialized:
        return None
    return (_frequency, _size, _channels_count)


def get_driver() -> str:
    return "ipython-html5" 


def get_sdl_mixer_version(linked: bool = True) -> tuple[int, int, int]:
    return (0, 0, 0)


def set_soundfont(paths: str | None = None) -> None:
    global _soundfont
    _soundfont = paths


def get_soundfont() -> str | None:
    return _soundfont


# channel mgmt

def get_num_channels() -> int:
    return _num_channels


def set_num_channels(count: int) -> None:
    global _num_channels
    _num_channels = max(0, int(count))


def set_reserved(count: int) -> int:
    global _reserved
    _reserved = max(0, min(int(count), _num_channels))
    return _reserved


def find_channel(force: bool = False) -> "Channel | None":
    """Return an inactive Channel, or *None*.

    If *force* is true, return the channel with the longest-playing sound.
    """
    for i in range(_reserved, _num_channels):
        ch = Channel(i)
        if not ch.get_busy():
            return ch
    if force and _num_channels > _reserved:
        return Channel(_reserved)
    return None


# global playback control

def get_busy() -> bool:
    for i in range(_num_channels):
        ch = _channel_pool.get(i)
        if ch is not None and ch.get_busy():
            return True
    return False


def stop() -> None:
    for ch in list(_channel_pool.values()):
        ch.stop()


def pause() -> None:
    for ch in list(_channel_pool.values()):
        ch.pause()


def unpause() -> None:
    for ch in list(_channel_pool.values()):
        ch.unpause()


def fadeout(time: int) -> None:
    for ch in list(_channel_pool.values()):
        ch.fadeout(time)


# Sound class

class Sound:
    """Represents a loaded audio sample.

    Parameters
    ----------
    file : str, Path, or file-like
        Path to a WAV / MP3 / OGG file.
    buffer : bytes
        Raw WAV bytes.
    array : numpy.ndarray
        NumPy PCM samples (``int16`` or ``float32``).
    """

    def __init__(
        self,
        file: FileLike | None = None,
        *,
        buffer: bytes | None = None,
        array: np.ndarray | None = None,
    ):
        if file is not None:
            if isinstance(file, (str, Path)):
                self._data_uri = _file_to_data_uri(file)
                p = Path(file)
                raw = p.read_bytes()
            else:
                raw = file.read()
                self._data_uri = _file_to_data_uri(io.BytesIO(raw))
            self._raw = raw
        elif buffer is not None:
            self._raw = bytes(buffer)
            b64 = base64.b64encode(self._raw).decode("ascii")
            self._data_uri = f"data:audio/wav;base64,{b64}"
        elif array is not None:
            wav = _array_to_wav_bytes(array, _frequency)
            self._raw = wav
            b64 = base64.b64encode(wav).decode("ascii")
            self._data_uri = f"data:audio/wav;base64,{b64}"
        else:
            raise TypeError(
                "Sound() requires a file, buffer, or array argument"
            )

        self._volume: float = 1.0
        self._length: float | None = None
        self._playing_on: set[int] = set()  # channel ids

    # -- playback ------------------------------------------------------------

    def play(self, loops: int = 0, maxtime: int = 0, fade_ms: int = 0) -> "Channel":
        """Play this Sound on an available channel.

        Returns the :class:`Channel` used.
        """
        ch = find_channel(force=True)
        if ch is None:
            ch = Channel(0)
        ch.play(self, loops=loops, maxtime=maxtime, fade_ms=fade_ms)
        return ch

    def stop(self) -> None:
        """Stop this Sound on all channels."""
        for ch_id in list(self._playing_on):
            ch = _channel_pool.get(ch_id)
            if ch is not None:
                ch.stop()

    def fadeout(self, time: int) -> None:
        for ch_id in list(self._playing_on):
            ch = _channel_pool.get(ch_id)
            if ch is not None:
                ch.fadeout(time)

    # volume

    def set_volume(self, value: float) -> None:
        self._volume = max(0.0, min(1.0, float(value)))

    def get_volume(self) -> float:
        return self._volume

    # info

    def get_num_channels(self) -> int:
        return len(self._playing_on)

    def get_length(self) -> float:
        """Duration in seconds."""
        if self._length is not None:
            return self._length
        try:
            with wave.open(io.BytesIO(self._raw)) as wf:
                self._length = wf.getnframes() / wf.getframerate()
        except Exception:
            self._length = 0.0
        return self._length

    def get_raw(self) -> bytes:
        return self._raw

    def copy(self) -> "Sound":
        s = Sound.__new__(Sound)
        s._data_uri = self._data_uri
        s._raw = self._raw
        s._volume = self._volume
        s._length = self._length
        s._playing_on = set()
        return s

    __copy__ = copy

    def __repr__(self) -> str:
        return f"<Sound(length={self.get_length():.2f}s)>"


# Channel class

class Channel:
    """Represents one audio playback channel."""

    def __new__(cls, id: int) -> "Channel":
        existing = _channel_pool.get(id)
        if existing is not None:
            return existing
        obj = super().__new__(cls)
        obj._id = id
        obj._sound: Sound | None = None
        obj._queued: Sound | None = None
        obj._volume: float = 1.0
        obj._busy: bool = False
        obj._paused: bool = False
        obj._endevent: int = _c.NOEVENT
        obj._element_id: str = ""
        _channel_pool[id] = obj
        return obj

    def __init__(self, id: int) -> None:
        pass

    @property
    def id(self) -> int:
        return self._id

    # playback

    def play(
        self,
        sound: Sound,
        loops: int = 0,
        maxtime: int = 0,
        fade_ms: int = 0,
    ) -> None:
        self.stop()

        self._sound = sound
        sound._playing_on.add(self._id)
        self._busy = True
        self._paused = False

        elem_id = f"ipygame_audio_{uuid.uuid4().hex[:12]}"
        self._element_id = elem_id

        # loop_attr = ' loop="true"' if loops == -1 else ""
        vol = max(0.0, min(1.0, sound._volume * self._volume))

        # create an <audio> element
        js_parts = [
            f'(function(){{',
            f'var a=document.createElement("audio");',
            f'a.id="{elem_id}";',
            f'a.src="{sound._data_uri}";',
            f'a.volume={vol:.4f};',
        ]

        # handle loops
        if loops == -1:
            js_parts.append('a.loop=true;')
        elif loops > 0:
            js_parts.append(f'a.dataset.loopsLeft={loops};')
            js_parts.append(
                'a.addEventListener("ended",function(){'
                'var n=parseInt(a.dataset.loopsLeft||"0");'
                'if(n>0){a.dataset.loopsLeft=n-1;a.currentTime=0;a.play();}'
                'else{a.remove();}'
                '});'
            )

        if loops == 0:
            js_parts.append(
                'a.addEventListener("ended",function(){a.remove();});'
            )

        # handle maxtime
        if maxtime > 0:
            js_parts.append(
                f'setTimeout(function(){{a.pause();a.remove();}},{maxtime});'
            )

        # handle fade-in
        if fade_ms > 0:
            js_parts.append(
                f'a.volume=0;'
                f'(function fade(){{var t={fade_ms},s=50,v=a.volume,step={vol:.4f}/(t/s);'
                f'var iv=setInterval(function(){{v=Math.min(v+step,{vol:.4f});'
                f'a.volume=v;if(v>={vol:.4f})clearInterval(iv);}},s);}})();'
            )

        # append to DOM and play
        js_parts.append(
            'document.body.appendChild(a);a.play().catch(function(){});'
        )
        js_parts.append('})();')

        _run_js("".join(js_parts))

    def stop(self) -> None:
        if self._sound is not None:
            self._sound._playing_on.discard(self._id)
        if self._element_id:
            # Remove the <audio> element from the DOM
            _run_js(
                f'(function(){{var a=document.getElementById("{self._element_id}");'
                f'if(a){{a.pause();a.remove();}}}})();'
            )
        self._sound = None
        self._busy = False
        self._paused = False
        self._element_id = ""

        if self._queued is not None:
            q = self._queued
            self._queued = None
            self.play(q)

    def pause(self) -> None:
        if self._element_id:
            # Pause the <audio> element
            _run_js(
                f'(function(){{var a=document.getElementById("{self._element_id}");'
                f'if(a)a.pause();}})();'
            )
        self._paused = True

    def unpause(self) -> None:
        if self._element_id:
            # Unpause (play) the <audio> element
            _run_js(
                f'(function(){{var a=document.getElementById("{self._element_id}");'
                f'if(a)a.play().catch(function(){{}});}})();'
            )
        self._paused = False

    def fadeout(self, time: int) -> None:
        if self._element_id:
            elem_id = self._element_id
            # Progressively reduce volume to 0, then pause and remove the <audio> element
            _run_js(
                f'(function(){{var a=document.getElementById("{elem_id}");'
                f'if(!a)return;var t={time},s=50,v=a.volume,step=v/(t/s);'
                f'var iv=setInterval(function(){{v=Math.max(v-step,0);'
                f'a.volume=v;if(v<=0){{clearInterval(iv);a.pause();a.remove();}}}},s);'
                f'}})();'
            )
        self._busy = False
        self._sound = None

    def queue(self, sound: Sound) -> None:
        self._queued = sound

    def get_queue(self) -> Sound | None:
        return self._queued

    # volume

    def set_volume(self, *args: float) -> None:
        if len(args) == 1:
            self._volume = max(0.0, min(1.0, float(args[0])))
        elif len(args) == 2:
            # Stereo: average for HTML5 (no per-ear control)
            self._volume = max(0.0, min(1.0, (float(args[0]) + float(args[1])) / 2))
        if self._element_id:
            _run_js(
                f'(function(){{var a=document.getElementById("{self._element_id}");'
                f'if(a)a.volume={self._volume:.4f};}})();'
            )

    def get_volume(self) -> float:
        return self._volume

    # state

    def get_busy(self) -> bool:
        return self._busy and not self._paused

    def get_sound(self) -> Sound | None:
        return self._sound

    def set_endevent(self, event_type: int = _c.NOEVENT) -> None:
        self._endevent = event_type

    def get_endevent(self) -> int:
        return self._endevent

    def set_source_location(self, angle: float, distance: float) -> None:
        """3D positioning not supported in HTML5 audio."""
        pass

    def __repr__(self) -> str:
        return f"<Channel({self._id})>"


# music sub-module

class _Music:
    """The ``mixer.music`` singleton - controls background music playback."""

    def __init__(self) -> None:
        self._data_uri: str | None = None
        self._raw: bytes | None = None
        self._volume: float = 1.0
        self._busy: bool = False
        self._paused: bool = False
        self._endevent: int = _c.NOEVENT
        self._element_id: str = ""
        self._pos_ms: int = 0

    # loading

    def load(self, file: FileLike, namehint: str = "") -> None:
        """Load a music file for playback."""
        self.stop()
        self._data_uri = _file_to_data_uri(file)
        if isinstance(file, (str, Path)):
            self._raw = Path(file).read_bytes()
        else:
            self._raw = file.read()

    def unload(self) -> None:
        self.stop()
        self._data_uri = None
        self._raw = None

    # playback

    def play(self, loops: int = 0, start: float = 0.0, fade_ms: int = 0) -> None:
        if self._data_uri is None:
            raise RuntimeError("No music loaded")

        self.stop()

        elem_id = f"ipygame_music_{uuid.uuid4().hex[:12]}"
        self._element_id = elem_id
        self._busy = True
        self._paused = False
        vol = self._volume


        js_parts = [
            f'(function(){{',
            f'var a=document.createElement("audio");',
            f'a.id="{elem_id}";',
            f'a.src="{self._data_uri}";',
            f'a.volume={vol:.4f};',
        ]

        if start > 0:
            js_parts.append(f'a.currentTime={start:.4f};')

        if loops == -1:
            js_parts.append('a.loop=true;')
        elif loops > 0:
            js_parts.append(f'a.dataset.loopsLeft={loops};')
            js_parts.append(
                'a.addEventListener("ended",function(){'
                'var n=parseInt(a.dataset.loopsLeft||"0");'
                'if(n>0){a.dataset.loopsLeft=n-1;a.currentTime=0;a.play();}'
                'else{a.remove();}'
                '});'
            )

        if loops == 0:
            js_parts.append(
                'a.addEventListener("ended",function(){a.remove();});'
            )

        if fade_ms > 0:
            js_parts.append(
                f'a.volume=0;'
                f'(function(){{var t={fade_ms},s=50,v=0,target={vol:.4f},step=target/(t/s);'
                f'var iv=setInterval(function(){{v=Math.min(v+step,target);'
                f'a.volume=v;if(v>=target)clearInterval(iv);}},s);}})();'
            )

        js_parts.append(
            'document.body.appendChild(a);a.play().catch(function(){});'
        )
        js_parts.append('})();')
        _run_js("".join(js_parts))

    def rewind(self) -> None:
        if self._element_id:
            _run_js(
                f'(function(){{var a=document.getElementById("{self._element_id}");'
                f'if(a)a.currentTime=0;}})();'
            )

    def stop(self) -> None:
        if self._element_id:
            _run_js(
                f'(function(){{var a=document.getElementById("{self._element_id}");'
                f'if(a){{a.pause();a.remove();}}}})();'
            )
        self._busy = False
        self._paused = False
        self._element_id = ""

    def pause(self) -> None:
        if self._element_id:
            _run_js(
                f'(function(){{var a=document.getElementById("{self._element_id}");'
                f'if(a)a.pause();}})();'
            )
        self._paused = True

    def unpause(self) -> None:
        if self._element_id:
            _run_js(
                f'(function(){{var a=document.getElementById("{self._element_id}");'
                f'if(a)a.play().catch(function(){{}});}})();'
            )
        self._paused = False

    def fadeout(self, time: int) -> None:
        if self._element_id:
            elem_id = self._element_id
            _run_js(
                f'(function(){{var a=document.getElementById("{elem_id}");'
                f'if(!a)return;var t={time},s=50,v=a.volume,step=v/(t/s);'
                f'var iv=setInterval(function(){{v=Math.max(v-step,0);'
                f'a.volume=v;if(v<=0){{clearInterval(iv);a.pause();a.remove();}}}},s);'
                f'}})();'
            )
        self._busy = False
        self._paused = False

    # volume

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, float(volume)))
        if self._element_id:
            _run_js(
                f'(function(){{var a=document.getElementById("{self._element_id}");'
                f'if(a)a.volume={self._volume:.4f};}})();'
            )

    def get_volume(self) -> float:
        return self._volume

    # state

    def get_busy(self) -> bool:
        return self._busy and not self._paused

    def set_pos(self, pos: float) -> None:
        if self._element_id:
            _run_js(
                f'(function(){{var a=document.getElementById("{self._element_id}");'
                f'if(a)a.currentTime={float(pos):.4f};}})();'
            )

    def get_pos(self) -> int:
        if not self._busy:
            return -1
        return 0  # idk

    def queue(self, file: FileLike, namehint: str = "", loops: int = 0) -> None:
        self._queued_uri = _file_to_data_uri(file)

    def set_endevent(self, event_type: int = _c.NOEVENT) -> None:
        self._endevent = event_type

    def get_endevent(self) -> int:
        return self._endevent

    def get_metadata(self, filename: FileLike | None = None, namehint: str = "") -> dict:
        return {"title": "", "album": "", "artist": "", "copyright": ""} # Not supported


# Module-level ``music`` attribute — a singleton.
music = _Music()
