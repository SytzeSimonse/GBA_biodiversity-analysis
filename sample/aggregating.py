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
from sample.pitfall import calculate_point_statistics_from_raster
from sample.helpers import sort_alphanumerically

import matplotlib.pyplot as plt
import numpy as np
from alive_progress import alive_bar
from sample.data_analysis import calculate_array_statistics, count_proportions_in_array
from sample.pitfall import calculate_point_statistics_from_raster_v2

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

            bounds, result_points, num_points = get_virtual_tile_point_date(
                col_off = col_off,
                row_off = row_off,
                raster = raster,
                tile_width = tile_size_x,
                tile_height = tile_size_y
            )

            if result == False or num_points == 0:
                continue

            found_traps = {
                "Number of traps": num_points
            }

            combined = {**bounds, **found_traps, **result, **result_points}

            data_table = data_table.append(combined, ignore_index = True)

        data_table.to_csv(args.output)

        # names = ['left', 'right', 'top', 'bottom']

        # id_dict = {
        #     "ID": data_table.index + 1
        # }

        # bounding_box_dict = dict(zip(names, bounding_box))
        # statistics = {**id_dict, **bounding_box_dict, **statistics}

        # res, num_points = calculate_point_statistics_from_raster_v2(
        #     bounding_box,
        #     point_csv_fpath = "data/raw/pitfall_TER.csv"
        # )

        # total_points_encountered += num_points
        
        # num_points_dict = {
        #     'number of traps': num_points
        # }

        # if res:
        #     statistics = {**statistics, **num_points_dict, **res}
        #     data_table = data_table.append(statistics, ignore_index=True)

        # data_table.to_csv(args.output)

    # with alive_bar(tiles_x * tiles_y * raster.count) as bar:
    #     for tile_x in range(0, tiles_x):
    #         for tile_y in range(0, tiles_y):
    #             tile_id += 1

    #             # Create empty dictionary for statistics
    #             statistics = {}

    #             # Loop through all bands for this chunk
    #             for band_no in range(16, 17):
    #                 # Add +1 to the progress bar
    #                 bar()
    #                 time.sleep(0.001)

    #                 # for col_off, row_off in offsets:
    #                     #     window = Window(col_off=col_off, row_off=row_off, width=tile_size_x, height=tile_size_y)
    #                     #     data = src.read(boundless=True, window=window, fill_value=fill_value)
    #                     #     print(data.shape)
    #                 # print(offsets)

    #                 print("(x1, y1) - (x2, y2) = ({},{}) - ({},{})".format(
    #                     (tile_x * tile_size_x),
    #                     (tile_y * tile_size_y),
    #                     ((tile_x + 1) * tile_size_x),
    #                     ((tile_y + 1) * tile_size_y)
    #                 ))

    #                 # Read the raster data for specific virtual tile
    #                 tile = raster.read(band_no)[
    #                     (tile_x * tile_size_x):((tile_x + 1) * tile_size_x),
    #                     (tile_y * tile_size_y):((tile_y + 1) * tile_size_y)
    #                 ]

    #                 print("Shape: {}".format(raster.read(band_no).shape))

    #                 if np.all(tile == np.nan):
    #                     print("Tile ({},{}) only contains NaN values.".format(tile_x, tile_y))
    #                     continue

    #                 # For the land use band, count proportions instad of array statistics
    #                 if band_no == args.land_use_band:
    #                     props = count_proportions_in_array(tile, "data/raw/classes.txt")
    #                     statistics = {**props, **statistics}

    #                     plt.imshow(tile)
    #                     plt.show()


    #                 if np.all(tile < -10_000_000):
    #                     continue

    #                 tile_statistics = calculate_array_statistics(tile)
    #                 temp = "band {} - ".format(band_no)

    #                 if tile_statistics:
    #                     tile_statistics_named = {temp + str(key): val for key, val in tile_statistics.items()}

    #                 statistics = {**statistics, **tile_statistics_named}

    #             bounding_box = [
    #                 int(raster.bounds[0] + tile_x * coords_size_x),
    #                 int(raster.bounds[0] + tile_x * coords_size_x + coords_size_x),
    #                 int(raster.bounds[1] + tile_y * coords_size_y),
    #                 int(raster.bounds[1] + tile_y * coords_size_y + coords_size_y),
    #             ]

    #             names = ['left', 'right', 'top', 'bottom']

    #             id_dict = {
    #                 "ID": data_table.index + 1
    #             }

    #             bounding_box_dict = dict(zip(names, bounding_box))
    #             statistics = {**id_dict, **bounding_box_dict, **statistics}

    #             res, num_points = calculate_point_statistics_from_raster_v2(
    #                 bounding_box,
    #                 point_csv_fpath = "data/raw/pitfall_TER.csv"
    #             )

    #             total_points_encountered += num_points
                
    #             num_points_dict = {
    #                 'number of traps': num_points
    #             }

    #             if res:
    #                 statistics = {**statistics, **num_points_dict, **res}
    #                 data_table = data_table.append(statistics, ignore_index=True)

    #             data_table.to_csv(args.output)

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
        band_data = raster.read(band_no, boundless = False, window = window, fill_value = 0)

        # If all values in the band are NaN, skip this tile
        if np.all(band_data == np.nan):
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

    result, num_points = calculate_point_statistics_from_raster_v2(
        bounding_box,
        point_csv_fpath = "data/raw/pitfall_TER.csv"
    )

    names = ['left', 'right', 'top', 'bottom']
    bounding_box_dict = dict(zip(names, bounding_box))

    return bounding_box_dict, result, num_points

if __name__ == '__main__':
    main()