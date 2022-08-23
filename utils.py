"""
pandastim/utils.py

Helper functions used in multiple classes in stimulu/textures

Part of pandastim package: https://github.com/mattdloring/pandastim
"""
import numpy as np
from scipy import signal

def sin_byte(X: np.array, freq: int = 1) -> np.array:
    """
    Creates unsigned 8 bit representation of sin (T_unsigned_Byte).
    """
    sin_float = np.sin(freq * X)

    # from 0-255
    sin_transformed = (sin_float + 1) * 127.5
    return np.uint8(sin_transformed)


def grating_byte(X: np.array, freq: int = 1) -> np.array:
    """
    Unsigned 8 bit representation of a grating (square wave)
    """
    grating_float = signal.square(X * freq)

    # from 0-255
    grating_transformed = (grating_float + 1) * 127.5
    return np.uint8(grating_transformed)


def card2uv(val: float) -> float:
    """
    from model (card) -based normalized device coordinates (-1,-1 bottom left, 1,1 top right)
    appropriate for cards to texture-based uv-coordinates.

    For more on these different coordinate systems for textures:
        https://docs.panda3d.org/1.10/python/programming/texturing/simple-texturing
    """
    return 0.5 * val


def uv2card(val: float) -> float:
    """
    Transform from texture-based uv-coordinates to card-based normalized device coordinates
    """
    return 2 * val


def unpack_tex(tex) -> dict:
    vdict = vars(tex).copy()
    try:
        del vdict["texture_array"]
    except KeyError:
        pass
    try:
        del vdict["texture"]
    except KeyError:
        pass
    return vdict
