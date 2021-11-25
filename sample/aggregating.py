import argparse
import os
import re
import math

import pandas as pd

from shapely.geometry import Point, point
from geopandas import GeoDataFrame

from tqdm import tqdm

import time

import rasterio as rio
from osgeo import gdal
from itertools import product, chain
from rasterio.windows import Window

from sample.data_analysis import calculate_raster_statistics, count_pixels_in_raster
from sample.pitfall import calculate_point_statistics_within_bounds
from sample.helpers import sort_alphanumerically

import matplotlib.pyplot as plt
import numpy as np
from alive_progress import alive_bar
from sample.data_analysis import calculate_array_statistics, count_proportions_in_array
from sample.pitfall import calculate_point_statistics_within_bounds

# Define constants
TOTAL_NUM_OF_TRAPS = 135

def main():
    parser = argparse.ArgumentParser(
        description = """This command aggregates data from a raster file."""
    )

    ## INPUT
    parser.add_argument('-r', '--raster',
        type = str,
        help='Filepath to raster',
        default='data/raw/combined.tif'
    )

    ## INPUT
    parser.add_argument('-d', '--dimension',
        type = str,
        help='Dimension of tiles (in metres)',
        default=4000
    )

    ## OUTPUT
    parser.add_argument('-o', '--output',
        type = str,
        help='Folder of data table',
        default="output/default.csv"
    )

    ## LAND USE BAND
    parser.add_argument('-lub', '--land-use-band',
        type = int,
        help = 'Number of band containing the land use data',
        default = 16
    )

    ## LAND USE LUT
    parser.add_argument('-lut', '--lookup-table',
        help='Filename of look-up table for land use classes (.txt file)',
        default='data/raw/classes.txt'
    )

    ## VERBOSITY
    parser.add_argument('-v', '--verbose',
        help='Verbose output',
        default=True
    )

    args = parser.parse_args()

    # For each tile:
    ## Get the land use pixel proportions, and;
    ## Get the statistics of the thematic variables;
    ## Get the statistics of the Sentinel-2 bands.

    # Open the raster
    raster = rio.open(args.raster)
    
    # Get raster cell sizes
    cell_size_x, cell_size_y = raster.res

    # Calculate tile size
    tile_size_x = int((int(args.dimension) / cell_size_x))
    tile_size_y = int((int(args.dimension) / cell_size_y))

    # Create the tile offsets
    offsets = product(range(0, raster.meta['width'], tile_size_x), range(0, raster.meta['height'], tile_size_y))

    # Set variable for fille values
    fill_value = 0

    # Calculate number of tiles necessary
    tiles_x = math.ceil(raster.width / tile_size_x)
    tiles_y = math.ceil(raster.height / tile_size_y)

    total_num_tiles = (tiles_x * tiles_y)

    print("You will have {} x {} = {} tiles in total.".format(
        tiles_x, tiles_y, total_num_tiles
    ))

    # Create counter variable for the amount of points (= traps) found, to verify its equal to total number of points
    total_points_encountered = 0

    # Create empty Pandas DataFrame for storing our aggregated data
    data_table = pd.DataFrame()

    with alive_bar(total_num_tiles) as bar:
        for index, (col_off, row_off) in enumerate(offsets):

            bar()

            result = create_virtual_tile_data(
                col_off = col_off,
                row_off = row_off,
                raster = raster,
                tile_width = tile_size_x,
                tile_height = tile_size_y
            )

            bounds, result_points = get_virtual_tile_point_date(
                col_off = col_off,
                row_off = row_off,
                raster = raster,
                tile_width = tile_size_x,
                tile_height = tile_size_y
            )

            print(result_points)
            if result == False or not result_points:
                continue

            combined = {**bounds, **result, **result_points}

            data_table = data_table.append(combined, ignore_index = True)

        data_table.to_csv(args.output)

    assert total_points_encountered == TOTAL_NUM_OF_TRAPS, "Only {} points out of {} points".format(
        total_points_encountered, TOTAL_NUM_OF_TRAPS
    )

    data_table.to_csv(args.output)

def create_virtual_tile_data(col_off, row_off, raster, tile_width, tile_height, land_use_band: int = 16, verbose = True) -> pd.Series:
    # Set window
    window = Window(col_off = col_off, row_off = row_off, width = tile_width, height = tile_height)

    # Create empty dictionary for land use proportions
    land_use_proportions = {}
    
    # Create empty dictionary for band statistics
    statistics = {}

    # Create a range for the bands to loop through, starting with the land use band
    band_order = chain(
        range(land_use_band, raster.count),
        range(1, land_use_band + 1)
    )

    # Loop through all bands for the tile
    for band_no in range(1, raster.count):
        # Read band data
        band_data = raster.read(band_no, boundless = False, window = window, fill_value = np.NaN)

        # If all values in the band are NaN, skip this tile
        if np.isnan(band_data).all():
            if verbose:
                print("Tile ({},{}) only contains NaN values.".format(col_off, row_off))
            return False

        # If all values are very negative, skip this tile
        # NOTE: With (supposedly) rasterio, the NaN values are assigned the largest possible negative value
        if np.all(band_data < -10_000_000):
            if verbose:
                print("The data in tile {} has only negative values.".format(window))
            return False

        # For the land use band, count proportions instad of array statistics
        if band_no == land_use_band:
            # Get land use proportions
            land_use_proportions = count_proportions_in_array(band_data, "data/raw/classes.txt")

            # If the tile only consists of the class 'clouds/shadows', skip this tile
            if land_use_proportions['clouds/shadows'] == 1:
                if verbose:
                    print("This tile has only clouds and/or shadows, and is therefore skipped.")
                return False

            statistics = {**land_use_proportions, **statistics}
            continue

        tile_statistics = calculate_array_statistics(band_data)
        temp = "band {} - ".format(band_no)

        if tile_statistics:
            tile_statistics_named = {temp + str(key): val for key, val in tile_statistics.items()}

        statistics = {**statistics, **tile_statistics_named}

    return statistics

def get_virtual_tile_point_date(raster, col_off, row_off, tile_width, tile_height):
    """[summary]

    Args:
        raster ([type]): [description]
    """
    # Calculate the number of tiles that fit in the raster
    tiles_x = math.ceil(raster.width / tile_width)
    tiles_y = math.ceil(raster.height / tile_height)

    # NOTE: bounds = left, bottom, right, top
    # Calculate the raster width, expressed in the CRS of the raster
    raster_width = int(raster.bounds[2] - raster.bounds[0])
    raster_height = int(raster.bounds[3] - raster.bounds[1])

    # Calculate the size of each tile in coordinates
    coords_size_x = raster_width / tiles_x
    coords_size_y = raster_height / tiles_y

    # Create bounding box
    bounding_box = [
        int(raster.bounds[0] + (col_off / tile_width) * coords_size_x),
        int(raster.bounds[0] + (col_off / tile_width) * coords_size_x + coords_size_x),
        int(raster.bounds[1] + (row_off / tile_height) * coords_size_y),
        int(raster.bounds[1] + (row_off / tile_height) * coords_size_y + coords_size_y),
    ]

    result = calculate_point_statistics_within_bounds(
        bounding_box,
        point_csv_fpath = "data/raw/pitfall_TER.csv"
    )

    names = ['x1', 'x2', 'y1', 'y2']
    bounding_box_dict = dict(zip(names, bounding_box))

    return bounding_box_dict, result

if __name__ == '__main__':
    main()