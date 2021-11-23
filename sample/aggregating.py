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
from itertools import product
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

    raster = rio.open(args.raster)
    fill_value = 0
    
    # Get raster cell size
    cell_size_x, cell_size_y = raster.res

    # Calculate tile size
    tile_size_x = int((int(args.dimension) / cell_size_x))
    tile_size_y = int((int(args.dimension) / cell_size_y))

    # Calculate number of tiles necessary
    tiles_x = math.ceil(raster.width / tile_size_x)
    tiles_y = math.ceil(raster.height / tile_size_y)

    print("You will have {} x {} = {} tiles in total.".format(
        tiles_x, tiles_y, tiles_x * tiles_y
    ))

    # NOTE: bounds = left, bottom, right, top
    # Calculate the raster width in coordinates
    raster_width = int(raster.bounds[2] - raster.bounds[0])
    raster_height = int(raster.bounds[3] - raster.bounds[1])

    # Calculate the size of each tile in coordinates
    coords_size_x = raster_width / tiles_x
    coords_size_y = raster_height / tiles_y

    # Create counter variable for the amount of points (= traps) found, to verify its equal to total number of points
    total_points_encountered = 0

    # Create empty Pandas DataFrame for storing our aggregated data
    data_table = pd.DataFrame()

    tile_id = 0

    with alive_bar(tiles_x * tiles_y * raster.count) as bar:
        for tile_x in range(0, tiles_x):
            for tile_y in range(0, tiles_y):
                tile_id += 1

                # Create empty dictionary for statistics
                statistics = {}

                # Loop through all bands for this chunk
                for band_no in range(16, 17):
                    # Add +1 to the progress bar
                    bar()
                    time.sleep(0.001)

                    # for col_off, row_off in offsets:
                        #     window = Window(col_off=col_off, row_off=row_off, width=tile_size_x, height=tile_size_y)
                        #     data = src.read(boundless=True, window=window, fill_value=fill_value)
                        #     print(data.shape)
                    # print(offsets)

                    print("(x1, y1) - (x2, y2) = ({},{}) - ({},{})".format(
                        (tile_x * tile_size_x),
                        (tile_y * tile_size_y),
                        ((tile_x + 1) * tile_size_x),
                        ((tile_y + 1) * tile_size_y)
                    ))

                    # Read the raster data for specific virtual tile
                    tile = raster.read(band_no)[
                        (tile_x * tile_size_x):((tile_x + 1) * tile_size_x),
                        (tile_y * tile_size_y):((tile_y + 1) * tile_size_y)
                    ]

                    print("Shape: {}".format(raster.read(band_no).shape))

                    if np.all(tile == np.nan):
                        print("Tile ({},{}) only contains NaN values.".format(tile_x, tile_y))
                        continue

                    # For the land use band, count proportions instad of array statistics
                    if band_no == args.land_use_band:
                        props = count_proportions_in_array(tile, "data/raw/classes.txt")
                        statistics = {**props, **statistics}

                        plt.imshow(tile)
                        plt.show()


                    if np.all(tile < -10_000_000):
                        continue

                    tile_statistics = calculate_array_statistics(tile)
                    temp = "band {} - ".format(band_no)

                    if tile_statistics:
                        tile_statistics_named = {temp + str(key): val for key, val in tile_statistics.items()}

                    statistics = {**statistics, **tile_statistics_named}

                bounding_box = [
                    int(raster.bounds[0] + tile_x * coords_size_x),
                    int(raster.bounds[0] + tile_x * coords_size_x + coords_size_x),
                    int(raster.bounds[1] + tile_y * coords_size_y),
                    int(raster.bounds[1] + tile_y * coords_size_y + coords_size_y),
                ]

                names = ['left', 'right', 'top', 'bottom']

                id_dict = {
                    "ID": data_table.index + 1
                }

                bounding_box_dict = dict(zip(names, bounding_box))
                statistics = {**id_dict, **bounding_box_dict, **statistics}

                res, num_points = calculate_point_statistics_from_raster_v2(
                    bounding_box,
                    point_csv_fpath = "data/raw/pitfall_TER.csv"
                )

                total_points_encountered += num_points
                
                num_points_dict = {
                    'number of traps': num_points
                }

                if res:
                    statistics = {**statistics, **num_points_dict, **res}
                    data_table = data_table.append(statistics, ignore_index=True)

                data_table.to_csv(args.output)

    print("Aggregating!")

    assert total_points_encountered == TOTAL_NUM_OF_TRAPS, "Only {} points out of {} points".format(
        total_points_encountered, TOTAL_NUM_OF_TRAPS
    )

    data_table.to_csv(args.output)

if __name__ == '__main__':
    main()