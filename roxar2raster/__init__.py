import io, sys

import numpy as np
import numpy.ma

from PIL import Image

import roxar_proxy as roxar

import xtgeo
import xtgeo.plot

__version__ = "0.3.0"

PAD_WIDTH = 2

def pad_frame(values):
    mask = values.mask
    mask = numpy.pad(mask, PAD_WIDTH, "constant", constant_values=True)
    return numpy.ma.masked_array(numpy.pad(values, PAD_WIDTH, "edge"), mask)

def pad_border(values):
    clipped_values = np.ma.filled(values, np.NaN)
    north = np.roll(clipped_values, 1, 0)
    south = np.roll(clipped_values, -1, 0)
    west = np.roll(clipped_values, 1, 1)
    east = np.roll(clipped_values, -1, 1)
    border = np.fmax(np.fmax(np.fmax(north, south), west), east)
    border_masked = np.ma.masked_invalid(border)
    padded = np.fmax(border, values.data)
    return np.ma.masked_array(padded, np.logical_and(values.mask, border_masked.mask))

def pad(values):
    padded = pad_border(pad_border(values))
    padded.mask = values.mask
    return pad_frame(padded)

def get_margin(values):
    clipped_values = np.ma.filled(values, np.NaN)
    margin = 2
    north = np.roll(clipped_values, margin, 0)
    south = np.roll(clipped_values, -margin, 0)
    west = np.roll(clipped_values, margin, 1)
    east = np.roll(clipped_values, -margin, 1)
    mask = north * south * west * east
    mask[~np.isnan(mask)] = 1.
    clipped_values *= mask
    mask = np.ma.masked_invalid(clipped_values)
    mask = np.ma.getmask(mask)
    return mask
    
def array2d_to_ieee_float(z_array):
    shape = z_array.shape

    z_array = z_array.astype(np.float32)

    z_array.fill_value = np.NaN

    z_array = np.ma.filled(z_array)

    byte_array = np.frombuffer(z_array.tobytes(), dtype=np.uint8)
    byte_array = byte_array.reshape((shape[0], shape[1], 4))

    image = Image.fromarray(byte_array, "RGBA")

    byte_io = io.BytesIO()
    image.save(byte_io, format="png")
    byte_io.seek(0)

    test_image = Image.open(byte_io)

    test_buffer = test_image.tobytes(encoder_name='raw')

    test_array = np.frombuffer(test_buffer, dtype=np.dtype('float32'))
    test_array = test_array.reshape((shape[0], shape[1]))

    byte_io.seek(0)

    assert(np.array_equal(test_array, z_array, equal_nan=True))

    return byte_io

def array2d_to_webviz_float(z_array):
    shape = z_array.shape

    z_array.fill_value = np.NaN

    z_array = np.ma.filled(z_array)

    z_array = np.repeat(z_array, 4)  # This will flatten the array

    z_array[0::4][np.isnan(z_array[0::4])] = 0  # Red
    z_array[1::4][np.isnan(z_array[1::4])] = 0  # Green
    z_array[2::4][np.isnan(z_array[2::4])] = 0  # Blue

    z_array[0::4] = np.floor((z_array[0::4] / (256 * 256)) % 256)  # Red
    z_array[1::4] = np.floor((z_array[1::4] / 256) % 256)  # Green
    z_array[2::4] = np.floor(z_array[2::4] % 256)  # Blue
    z_array[3::4] = np.log10(z_array[3::4])

    # Back to 2d shape + 1 dimension for the rgba values.
    image = Image.fromarray(np.uint8(z_array), "RGBA")

    byte_io = io.BytesIO()
    image.save(byte_io, format="png")
    byte_io.seek(0)

    return byte_io

def array2d_to_png(z_array, z_offset=0., z_scale=1., margin=np.ma.masked_array.mask):
    """The DeckGL map dash component takes in pictures as base64 data
    (or as a link to an existing hosted image). I.e. for containers wanting
    to create pictures on-the-fly from numpy arrays, they have to be converted
    to base64. This is an example function of how that can be done.

    This function encodes the numpy array to a RGBA png.
    The array is encoded as a heightmap, in a format similar to Mapbox TerrainRGB
    (https://docs.mapbox.com/help/troubleshooting/access-elevation-data/),
    but without the -10000 offset and the 0.1 scale.
    The undefined values are set as having alpha = 0. The height values are
    shifted to start from 0.
    """

    shape = z_array.shape

    z_array.fill_value = np.NaN

    z_array += z_offset

    z_array *= z_scale

    unfilled = z_array.copy()
    unfilled.mask = False

    if margin.any():
        z_array.mask = margin
    z_array = np.ma.filled(z_array)

    max_value = np.nanmax(z_array)
    min_value = np.nanmin(z_array)
    mean_value = (min_value + max_value) * .5

    z_array = np.repeat(z_array, 4)  # This will flatten the array
    unfilled = np.repeat(unfilled, 4)  # This will flatten the array

    z_array[0::4] = np.floor((unfilled[0::4] / (256 * 256)) % 256)  # Red
    z_array[1::4] = np.floor((unfilled[1::4] / 256) % 256)  # Green
    z_array[2::4] = np.floor(unfilled[2::4] % 256)  # Blue
    z_array[3::4] = np.where(np.isnan(z_array[3::4]), 250, 255)  # Alpha

    # Back to 2d shape + 1 dimension for the rgba values.
    z_array = z_array.reshape((shape[0], shape[1], 4))
    unfilled = unfilled.reshape((shape[0], shape[1], 4))

    image = Image.fromarray(np.uint8(z_array), "RGBA")

    byte_io = io.BytesIO()
    image.save(byte_io, format="png")
    byte_io.seek(0)

    return byte_io

def get_surface(project, name, category, stype):
    stream = io.BytesIO()
    surface = xtgeo.surface_from_roxar(project, name, category, stype=stype)
    surface.quickplot(filename=stream)
    return stream

def get_surface_normalized(project, name, category, stype):
    surface = xtgeo.surface_from_roxar(project, name, category, stype=stype)
    values = surface.values
    margin = get_margin(surface.values)
    min_value = np.nanmin(surface.values)
    max_value = np.nanmax(surface.values)
    scale_factor = (256 * 256 * 256 - 1) / (max_value - min_value)
    return array2d_to_png((values - min_value) * scale_factor, margin=margin)

def get_surface_absolute(project, name, category, stype):
    surface = xtgeo.surface_from_roxar(project, name, category, stype=stype)
    return array2d_to_png(surface.values, z_offset=0, z_scale=1)

def get_surface_webviz_float(project, name, category, stype):
    surface = xtgeo.surface_from_roxar(project, name, category, stype=stype)
    return array2d_to_webviz_float(surface.values)

def get_surface_ieee_float(project, name, category, stype):
    surface = xtgeo.surface_from_roxar(project, name, category, stype=stype)
    return array2d_to_ieee_float(surface.values)

