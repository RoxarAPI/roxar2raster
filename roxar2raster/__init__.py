import io, sys

import numpy as np
import numpy.ma

from PIL import Image

from roxar2json import roxar_proxy as roxar
import roxarlib
import roxarlib.structure_rms13 as roxstruct
import roxarlib.data2model

import xtgeo
import xtgeo.plot

__version__ = "0.0.1"

def clip(values):
    margin = 10
    north = np.roll(values, margin, 0)
    south = np.roll(values, -margin, 0)
    west = np.roll(values, margin, 1)
    east = np.roll(values, -margin, 1)
    mask = north * south * west * east
    mask[~np.isnan(mask)] = 1.
    values *= mask
    
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

def array2d_to_png(z_array, z_offset=0., z_scale=1.):
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

    z_array = np.ma.filled(z_array)

    z_array = np.repeat(z_array, 4)  # This will flatten the array

    z_array[0::4][np.isnan(z_array[0::4])] = 0  # Red
    z_array[1::4][np.isnan(z_array[1::4])] = 0  # Green
    z_array[2::4][np.isnan(z_array[2::4])] = 0  # Blue

    z_array[0::4] = np.floor((z_array[0::4] / (256 * 256)) % 256)  # Red
    z_array[1::4] = np.floor((z_array[1::4] / 256) % 256)  # Green
    z_array[2::4] = np.floor(z_array[2::4] % 256)  # Blue
    z_array[3::4] = np.where(np.isnan(z_array[3::4]), 0, 255)  # Alpha

    # Back to 2d shape + 1 dimension for the rgba values.
    z_array = z_array.reshape((shape[0], shape[1], 4))
    image = Image.fromarray(np.uint8(z_array), "RGBA")

    byte_io = io.BytesIO()
    image.save(byte_io, format="png")
    byte_io.seek(0)

    return byte_io

def get_structural_model(project):
    realization = 1

    hm = project.structural_models['DepthModelFromHUM'].horizon_models['GeologicHorizons']

    model_geometry = hm.get_geometry(realization)
    print(help(model_geometry))


    bbox = hm.get_bounding_box()
    v0 = bbox[0]
    v2 = bbox[1]
    fence = [v0, v2]
    z_min_max = (v0[2], v2[2])

    image_size = (500, 1000) # using matrix indexing: rows, columns
    image = roxstruct.create_fence_image(fence, z_min_max, hm.get_geometry(1), image_size=image_size)

    return image

def get_surface(project, name, category, stype, margin):
    stream = io.BytesIO()
    sys.stderr.write("Error: margin not supported.")
    sys.stderr.flush()
    if margin:
        return stream
    surface = xtgeo.surface_from_roxar(project, name, category, stype=stype)
    surface.quickplot(filename=stream)
    return stream

def get_surface_normalized(project, name, category, stype, margin):
    surface = xtgeo.surface_from_roxar(project, name, category, stype=stype)
    if margin:
        clip(surface.values)
    min_value = np.nanmin(surface.values)
    max_value = np.nanmax(surface.values)
    scale_factor = (256 * 256 * 256 - 1) / (max_value - min_value)
    return array2d_to_png((surface.values - min_value) * scale_factor)

def get_surface_absolute(project, name, category, stype, margin):
    surface = xtgeo.surface_from_roxar(project, name, category, stype=stype)
    if margin:
        clip(surface.values)
    return array2d_to_png(surface.values, z_offset=0, z_scale=1)

def get_surface_webviz_float(project, name, category, stype, margin):
    surface = xtgeo.surface_from_roxar(project, name, category, stype=stype)
    if margin:
        clip(surface.values)
    return array2d_to_webviz_float(surface.values)

def get_surface_ieee_float(project, name, category, stype, margin):
    surface = xtgeo.surface_from_roxar(project, name, category, stype=stype)
    if margin:
        clip(surface.values)
    return array2d_to_ieee_float(surface.values)

