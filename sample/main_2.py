import rasterio

from rasterio.plot import show

import pandas as pd
import numpy as np

import geopandas 

import os
import math

data_dir = "data"
raster_fname = "landuse_Behrmann.tif"

# Create dictionary for land use classes 
land_use_class_dict = {
    1: 'clouds/shadows',
    2: 'urban',
    3: 'bare_soil',
    4: 'other_crops',
    5: 'erica',
    6: 'arable_crops',
    7: 'pittosporum',
    8: 'eucalyptus',
    9: 'acacia',
    10: 'peatlands',
    11: 'pinus',
    12: 'cryptomeria',
    13: 'shrub_peatlands',
    14: 'calluna_juniperus',
    15: 'juniperus_ilex'
}

def split_raster(raster_fname, dimension: int = 5000, spatial_resolution: int = 20, verbose = True):
    """Splits raster in smaller quadrants.

    Args:
        raster ([type]): [description]
        resolution ([type]): [description]
    """
    # Open raster
    raster = rasterio.open(raster_fname)

    if verbose:
        print(raster.crs)

    # Calculate the tile size in pixels
    tile_pixel_size = int(dimension / spatial_resolution)
    
    # Calculate number of tiles in width and length
    num_tiles_x = math.ceil(raster.width / tile_pixel_size)
    num_tiles_y = math.ceil(raster.height / tile_pixel_size)

    # Calculate size of raster to fit in entire tiles (and not stay with leftover pixels)
    new_raster_size_x = raster.width + (tile_pixel_size - raster.width % tile_pixel_size)
    new_raster_size_y = raster.height + (tile_pixel_size - raster.height % tile_pixel_size)
    
    if verbose:
        print("New raster size (x,y): {},{}".format(new_raster_size_x, new_raster_size_y))

    # Calculate padding 
    padding_x = int((new_raster_size_x - raster.width) / 2)
    padding_y = int((new_raster_size_y - raster.height) / 2)

    if verbose:
        print("Padding X: {}".format(padding_x))
        print("Padding Y: {}".format(padding_y))

    # Read the band
    raster_band = raster.read(1)

    # Increment all values by 1
    ## -> Shifting the values, so '0' becomes available for NaN data.
    raster_band = raster_band + 1

    # Add padding ('0') to raster
    ## -> Creating space to fit in all the tiles
    padded_raster = np.pad(raster_band, pad_width = ((padding_y, padding_y), (padding_x, padding_x)))

    # Calculate total number of quadrants
    total_num_tiles = num_tiles_x * num_tiles_y

    # Create Pandas DataFrame
    data_table = pd.DataFrame(columns = list(land_use_class_dict.values()))

    # Create GeoPandas DataFrame for storing the tiles
    gpd_data_table =  geopandas.GeoDataFrame(data_table)
    print(gpd_data_table)

    # Initiate counter
    counter = 0

    # Calculate buffer 
    for x in range(0, num_tiles_x):
        for y in range(0, num_tiles_y):
            # TODO: Create polygons for the tiles


            # Showing raster
            # print("tile {}:{},{}:{}".format(
            #     x * tile_pixel_size, 
            #     (x + 1) * tile_pixel_size, 
            #     y * tile_pixel_size,
            #     (y + 1) * tile_pixel_size
            #     ))

            # Slice tile
            tile = padded_raster[
                y * tile_pixel_size:(y + 1) * tile_pixel_size,
                x * tile_pixel_size:(x + 1) * tile_pixel_size
            ]

            # Count the pixels
            pixel_count = count_pixels_in_tile(tile)
            print(pixel_count)
            data_table.loc[len(data_table)] = pixel_count

            if not pixel_count[0] == 1:
                show(tile)

            # Increment counter
            counter += 1

        print(data_table)

def count_pixels_in_tile(tile):
    # Calculate the total tile size
    tile_total_size = tile.shape[0] ** 2

    # Count the pixels
    pixel_counts = np.bincount(tile.flatten(), minlength = len(land_use_class_dict) + 1)

    non_zero_pixels = tile_total_size - pixel_counts[0]

    pixel_counts = np.round(
        np.true_divide(pixel_counts[1:], non_zero_pixels),
        2)

    if np.sum(pixel_counts) > 1:
        print(pixel_counts[1:])

    return pixel_counts
