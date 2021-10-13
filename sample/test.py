from itertools import product
from rasterio import windows

import rasterio as rio

import numpy as np

import os

in_path = 'data/'
input_filename = 'landuse.tif'

out_path = 'output/'
output_filename = 'tile_{}-{}.tif'

def get_tiles(ds, width = 256, height = 256):
    nols, nrows = ds.meta['width'], ds.meta['height']
    offsets = product(range(0, nols, width), range(0, nrows, height))
    big_window = windows.Window(col_off=0, row_off=0, width=nols, height=nrows)
    for col_off, row_off in  offsets:
        window = windows.Window(col_off=col_off, row_off=row_off, width=width, height=height).intersection(big_window)
        transform = windows.transform(window, ds.transform)
        yield window, transform

def add_padding_to_raster(raster_in, raster_out, padding = [1000,1,500,1]):
    """Adds a padding to raster.

    Args:
        raster ([type]): [description]

    Returns:
        raster: [description]
    """
    # Open raster
    raster = rio.open(raster_in)

    # Create list for bands
    padded_bands = []

    # Copy metadata
    out_meta = raster.meta.copy()

    # Loop through raster bands
    for band_no in range(1, raster.count + 1):
        # Read band
        raster_band = raster.read(band_no)

        # Add padding
        padded_raster_band = np.pad(raster_band, pad_width = ((padding[0], padding[1]), (padding[2], padding[3])))

        # Append padded raster band to list
        padded_bands.append(padded_raster_band)

    with rio.open(raster_out, 'w', **out_meta) as dest:
        for band_nr, src in enumerate(padded_bands, start=1):
            dest.write(src, band_nr)

add_padding_to_raster(
    raster_in = os.path.join(in_path, input_filename),
    raster_out = os.path.join('rasters', 'padded_landuse.tif'))

with rio.open(os.path.join(in_path, input_filename)) as inds:
    spatial_resolution = inds.profile['transform'][0]
    print("The spatial resolution of '{}' is {} {}(s).".format(
        input_filename,
        spatial_resolution, 
        inds.crs.linear_units))

    dimension = 2000

    tile_size = int(dimension / spatial_resolution)
    print(tile_size)

    tile_width, tile_height = 256, 256

    meta = inds.meta.copy()

    for window, transform in get_tiles(inds, width = tile_size, height = tile_size):
        #print(window)
        meta['transform'] = transform
        meta['width'], meta['height'] = window.width, window.height
        outpath = os.path.join(out_path,output_filename.format(int(window.col_off), int(window.row_off)))
        with rio.open(outpath, 'w', **meta) as outds:
            outds.write(inds.read(window=window))