"""
Module for manipulating rasters, including adding padding to and splitting rasters.
"""
import rasterio as rio
from itertools import product
from rasterio import band, windows

from rasterio.windows import Window

import numpy as np

import math
import os

import rasterio

from osgeo import gdal

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
    assert type(dimension) == int, "The dimension has to be provided as integer."
    assert os.path.exists(raster_in), "The file '{}' does not exist.".format(raster_in)

    # Open raster
    raster = rio.open(raster_in)

    # Get spatial resolution of raster
    raster_spatial_resolution = get_spatial_resolution_raster(raster_in)

    # Calculate resolution of tile in pixels
    tile_resolution = dimension / raster_spatial_resolution

    # Create list for bands
    padded_bands = []

    # Copy metadata
    out_meta = raster.meta.copy()

    # Determine padding based on spatial resolution of raster
    new_raster_width = raster.width + (tile_resolution - raster.width % tile_resolution)
    new_raster_height = raster.height + (tile_resolution - raster.height % tile_resolution)

    if verbose:
        print("The raster width will be increased from {} to {} pixels.".format(raster.width, new_raster_width))
        print("The raster height will be increased from {} to {} pixels.\n".format(raster.height, new_raster_height))

    # Determine padding
    padding_x = int(new_raster_width - raster.width)
    padding_y = int(new_raster_height - raster.height)

    # Update values based on padding
    out_meta.update({
        'width': new_raster_width,
        'height': new_raster_height
    })

    # Loop through raster bands
    for band_no in range(1, raster.count + 1):
        print("Processing band no. {}...".format(band_no))

        # Read band
        raster_band = raster.read(band_no)

        # Add padding
        padded_raster_band = np.pad(
            raster_band, 
            pad_width = ((0, padding_y), (0, padding_x)), 
            mode = 'constant',
            constant_values = 0)

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
    if os.path.exists(raster_fpath):
        assert os.path.splitext(raster_fpath)[1] == '.tif', "The file should be .tif format."

        # Open raster
        with rio.open(raster_fpath) as inds:
            spatial_resolution = inds.profile['transform'][0]

            if verbose:
                print("The spatial resolution of '{}' is {} {}(s).".format(
                    raster_fpath,
                    spatial_resolution, 
                    inds.crs.linear_units))

            return spatial_resolution
    else:
        raise FileNotFoundError(
            "The raster file does not exist."
        )

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

    # CHeck if output folder exists
    if not os.path.exists(raster_out):
        if verbose:
            print("Creating new folder for tiles...")
        os.mkdir("data/intermediate/tiles")

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
            outpath = os.path.join(raster_out, output_filename.format(int(window.col_off), int(window.row_off)))
            with rio.open(outpath, 'w', **meta) as outds:
                outds.write(raster.read(window = window))

def delete_single_value_tiles(tiles_folder: str) -> None:
    """Deletes raster files with only a single-value.

    Args:
        tiles_folder (str): Folder of rasters.
    """
    # Loop through tiles
    for tile in os.listdir(tiles_folder):
        # Combine paths of input folder and raster filename
        f = os.path.join(tiles_folder, tile)

        # If tile exists ...
        if os.path.isfile(f) and os.path.splitext(f)[1] == ".tif":

            # Open raster and read band
            raster = rio.open(f)
            raster_band = raster.read(1)
            
            # If all values are the same, remove file
            if (np.all(raster_band == raster_band[0])):
                os.remove(f)

def set_band_descriptions(raster_fpath: str, bands_txt: str) -> None:
    """Sets descriptions of raster bands using a .txt file.

    Args:
        raster_fpath (str): Filepath of raster.
        bands_txt (str): Filepath of .txt file with band names.
    """
    # Open raster using GDAL
    ds = gdal.Open(raster_fpath, gdal.GA_Update)

    # Open .txt file
    band_file = open(bands_txt, "r")

    # Splitting the content by comma
    bands = band_file.read().split(sep = ",")

    # Loop through all bands
    for band in range(1, len(bands)+1):
        rb = ds.GetRasterBand(band)
        rb.SetDescription(bands[band - 1])

    # Delete dataset    
    del ds

def combine_rasters(rasters: list):
    print("There are {} rasters to be combined.".format(len(rasters)))
    
    for raster_fpath in rasters:
        raster = rio.open(raster_fpath)

        for band in range(1, raster.count):
            print(band)