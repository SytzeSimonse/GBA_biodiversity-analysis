import argparse
import os
import re
import math

import pandas as pd

from shapely.geometry import Point, point
from geopandas import GeoDataFrame

from tqdm import tqdm

import rasterio as rio
from osgeo import gdal

from sample.data_analysis import calculate_raster_statistics, count_pixels_in_raster
from sample.pitfall import calculate_point_statistics_from_raster
from sample.helpers import sort_alphanumerically

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

    print(raster.bounds)

    import matplotlib.pyplot as plt
    import numpy as np
    from alive_progress import alive_bar
    from sample.data_analysis import calculate_array_statistics, count_proportions_in_array
    from sample.pitfall import calculate_point_statistics_from_raster_v2

    my_data = pd.DataFrame()

    with alive_bar(tiles_x * tiles_y) as bar:
        for tile_x in range(0, tiles_x):
            for tile_y in range(0, tiles_y):
                # Create empty dictionary for statistics
                statistics = {}

                # Loop through all bands for this chunk
                for band_no in range(1, 2):
                    bar()

                    tile = raster.read(band_no)[
                        (tile_x * tile_size_x):((tile_x + 1) * tile_size_x),
                        (tile_y * tile_size_y):((tile_y + 1) * tile_size_y)
                        ]

                    if band_no == args.land_use_band:
                        props = count_proportions_in_array(tile, "data/raw/classes.txt")
                        statistics = {**props, **statistics}

                    if np.all(tile < -10_000_000):
                        continue

                    tile_statistics = calculate_array_statistics(tile)
                    temp = "band {} - ".format(band_no)
                    tile_statistics_named = {temp + str(key): val for key, val in tile_statistics.items()}

                    statistics = {**statistics, **tile_statistics_named}

                # NOTE: bounds = left, bottom, right, top
                raster_width = int(raster.bounds[2] - raster.bounds[0])
                raster_height = int(raster.bounds[3] - raster.bounds[1])

                coords_size_x = raster_width / tiles_x
                coords_size_y = raster_height / tiles_y

                bounding_box = [
                    int(raster.bounds[0] + tile_x * coords_size_x),
                    int(raster.bounds[0] + tile_x * coords_size_x + coords_size_x),
                    int(raster.bounds[1] + tile_y * coords_size_y),
                    int(raster.bounds[1] + tile_y * coords_size_y + coords_size_y),
                ]

                res = calculate_point_statistics_from_raster_v2(
                    bounding_box,
                    point_csv_fpath = "data/raw/pitfall_TER.csv"
                )

                if res:
                    statistics = {**statistics, **res}
                    my_data = my_data.append(statistics, ignore_index=True)

    print("Aggregating!")
    my_data.to_csv("testing.csv")

if __name__ == '__main__':
    main()