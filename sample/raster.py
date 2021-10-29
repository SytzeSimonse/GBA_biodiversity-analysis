"""
Module for manipulating rasters, including adding padding to and splitting rasters.
"""
import rasterio as rio
from itertools import product
from rasterio import windows

import numpy as np

import math
import os

import rasterio

def determine_padding(raster_fpath, dimension, verbose = True) -> list:
    # Open raster
    raster = rio.open(raster_fpath)

    # Extract spatial resolution of raster
    spatial_resolution = get_spatial_resolution_raster(raster_fpath, verbose = True)

    # Calculate tile size (in pixels)
    tile_size = int(dimension / spatial_resolution)
    print("Tile size: {}".format(tile_size))

    new_raster_size_x = round(raster.width, tile_size)
    
    # Calculate number of tiles in width and length
    num_tiles_x = math.ceil(raster.width / tile_size)
    num_tiles_y = math.ceil(raster.height / tile_size)

    if verbose:
        print("With a dimension of {}, you can fit (x,y) ({},{}) tiles.".format(
            dimension, num_tiles_x, num_tiles_y
        ))

    # Calculate size of raster to fit in entire tiles (and not stay with leftover pixels)
    new_raster_size_x = raster.width + (tile_size - raster.width % tile_size)
    new_raster_size_y = raster.height + (tile_size - raster.height % tile_size)
    
    if verbose:
        print("New raster size (x,y): {},{}".format(new_raster_size_x, new_raster_size_y))

    # Calculate padding 
    padding_x = int((new_raster_size_x - raster.width) / 2)
    padding_y = int((new_raster_size_y - raster.height) / 2)

    if verbose:
        print("In width: {} -> {}".format(raster.width, raster.width + padding_x) * 2)
        print("In height: {} -> {}".format(raster.height, raster.height + padding_y * 2))

    return (padding_x, padding_y)

def add_padding_to_raster(raster_in: str, raster_out: str, dimension: int, verbose = True):
    """Adds a padding to the raster, based on the dimension of the tiles.

    Args:
        raster_in (str): Filename of input raster.
        raster_out (str): Filename of output raster.
        dimension (int): Dimension of tiles.

    Example:
        The raster is 118 x 135 and has a spatial resolution of 10 metre.
        The dimension of the tiles is set at 1 kilometre, which is 100 pixels (1000 / 10).
        The raster covers an area of 1180 x 1350 metre.
        The padding should therefore be (x,y): 10, 25. 
        This would give a raster of 1180 + 2 * 10 = 1200 and 1350 + 2 * 25 = 1400.
    """
    # Open raster
    raster = rio.open(raster_in)

    # Create list for bands
    padded_bands = []

    # Copy metadata
    out_meta = raster.meta.copy()

    # Get spatial resolution of raster
    raster_spatial_resolution = get_spatial_resolution_raster(raster_in)

    # Calculate resolution of tile in pixels
    tile_resolution = dimension / raster_spatial_resolution

    # Determine padding based on spatial resolution of raster
    new_raster_width = raster.width + (tile_resolution - raster.width % tile_resolution)
    new_raster_height = raster.height + (tile_resolution - raster.height % tile_resolution)

    if verbose:
        print("The raster width will be increased from {} to {} pixels.".format(raster.width, new_raster_width))
        print("The raster height will be increased from {} to {} pixels.".format(raster.height, new_raster_height))

    # Update values based on padding
    out_meta.update({
        'width': new_raster_width,
        'height': new_raster_height
    })

    # Determine padding
    padding = determine_padding(raster_in, dimension)

    # Loop through raster bands
    for band_no in range(1, raster.count + 1):
        # Read band
        raster_band = raster.read(band_no)

        # Add padding
        padded_raster_band = np.pad(
            raster_band, 
            pad_width = determine_padding(raster_in), 
            mode = 'constant',
            constant_values = (0))

        # Append padded raster band to list
        padded_bands.append(padded_raster_band)

    with rio.open(raster_out, 'w', **out_meta) as dest:
        for band_nr, src in enumerate(padded_bands, start=1):
            dest.write(src, band_nr)

def get_spatial_resolution_raster(raster_fpath, verbose = False) -> float:
    """Extracts spatial resolution from raster.

    Args:
        raster_fpath (str): Filepath of raster file.
        verbose (bool): Verbose output.

    Returns:
        float: Spatial resolution.
    """
    # Open raster
    with rio.open(raster_fpath) as inds:
        spatial_resolution = inds.profile['transform'][0]

        if verbose:
            print("The spatial resolution of '{}' is {} {}(s).".format(
                raster_fpath,
                spatial_resolution, 
                inds.crs.linear_units))

        return spatial_resolution





def get_tiles(ds, width = 256, height = 256):
    nols, nrows = ds.meta['width'], ds.meta['height']
    offsets = product(range(0, nols, width), range(0, nrows, height))
    big_window = windows.Window(col_off=0, row_off=0, width=nols, height=nrows)
    for col_off, row_off in  offsets:
        window = windows.Window(col_off=col_off, row_off=row_off, width=width, height=height).intersection(big_window)
        transform = windows.transform(window, ds.transform)
        yield window, transform

def tile_raster(raster_in, raster_out, dimension: int = 5000, verbose = True):
    """Splits raster in smaller tiles.

    Args:
        raster ([type]): [description]
        resolution ([type]): [description]
    """
    # Check if raster exists
    if not os.path.exists(raster_in):
        raise FileNotFoundError(
            "The file '{}' could not be found.".format(raster_in)
        )

    # Open raster
    with rio.open(raster_in) as raster:
        if verbose:
            print('The CRS of {} is {}.'.format(raster_in, raster.crs))

        # Get spatial resolution
        spatial_resolution = get_spatial_resolution_raster(raster_in)

        # Calculate the tile size in pixels
        tile_pixel_size = int(dimension / spatial_resolution)
        
        # Calculate number of tiles in width and length
        num_tiles_x = math.ceil(raster.width / tile_pixel_size)
        num_tiles_y = math.ceil(raster.height / tile_pixel_size)

        if verbose:
            print("There will be created {} tiles in total (width: {}, height: {}".format(
                num_tiles_x * num_tiles_y,
                num_tiles_x,
                num_tiles_y
            ))

        meta = raster.meta.copy()

        for window, transform in get_tiles(raster, width = tile_pixel_size, height = tile_pixel_size):
            meta['transform'] = transform
            meta['width'], meta['height'] = window.width, window.height
            output_filename = 'tile_{}-{}.tif'
            outpath = os.path.join(raster_out,output_filename.format(int(window.col_off), int(window.row_off)))
            with rio.open(outpath, 'w', **meta) as outds:
                outds.write(raster.read(window = window))