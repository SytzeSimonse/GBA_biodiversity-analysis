import argparse
import os
import re

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
        description = """This command creates a CSV file from a set of tiles (.tif rasters)"""
    )

    ## INPUT
    parser.add_argument('-t', '--tiles',
        type = str,
        help='Directory of tiles',
        default='data/intermediate/tiles'
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

    ## BAND NAMES
    parser.add_argument('-b', '--band-names',
        help='Names of raster bands (as .txt)',
        default='data/raw/bands.txt'
    )

    ## VERBOSITY
    parser.add_argument('-v', '--verbose',
        help='Verbose output',
        default=True
    )

    args = parser.parse_args()
          
    # Create an empty dataframe
    aggregated_df = pd.DataFrame()

    # For each tile:
    ## Get the land use pixel proportions, and;
    ## Get the statistics of the thematic variables;
    ## Get the statistics of the Sentinel-2 bands.

    # Sort the list of tile filenames as displayed in file systems
    tile_fnames = sort_alphanumerically(os.listdir(args.tiles))

    # Loop through all the tiles
    for tile_no in tqdm(range(len(tile_fnames)), desc = "Processing tiles..."):
        # Join path of folder and tile filename
        f = os.path.join(args.tiles, tile_fnames[tile_no])

        # Check if 
        if os.path.isfile(f) and os.path.splitext(f)[1] == '.tif':
            try:
                # Open tile
                tile = rio.open(f)
            except FileNotFoundError:
                print("The file '{}' does not exist.".format(f))

            # Get land use proportions (as dict)
            land_use_pixel_counts = count_pixels_in_raster(f, lut_fpath = args.lookup_table, band_no = 16)

            # Skip tiles which solely consist of clouds/shadows
            if land_use_pixel_counts['clouds/shadows'] == 1:
                continue

            # Create combined dictionary for all thematic band statistics
            thematic_band_statistics_combined = {}

            # Loop through all the thematic variables
            for band in range(1, tile.count + 1):
                # Skip the band with land use classes
                if band == args.land_use_band:
                    continue

                # Calculate raster statistics for single band
                thematic_var_statistics = calculate_raster_statistics(f, band)

                # If there is no available data, skip this band
                if thematic_var_statistics == None:
                    continue

                # Add calculated raster statistics to combined dictionary
                thematic_band_statistics_combined = {**thematic_band_statistics_combined, **thematic_var_statistics}

            # Calculate statistics of point data (as dict)          
            point_stats = calculate_point_statistics_from_raster(
                raster_fpath = f,
                point_csv_fpath = 'data/raw/pitfall_TER.csv'
            )

            # If no point stats are found, continue loop
            if not point_stats:
                continue

            # Create an ID (as dict)
            identifier = {
                'ID': int(tile_no) + 1
            }

            # Create dict for filename
            filename_dict = {
                'filename': f
            }

            # Create dict for coordinates of tile
            tile_extent_dict = {
                'left': tile.bounds[0],
                'top': tile.bounds[3]
            }

            # Create dict for CRS
            tile_crs = {
                'crs': tile.crs
            }
                           
            # Combine the dictionaries as Series
            combined = pd.Series({
                **filename_dict,
                **tile_extent_dict,
                **identifier, 
                **land_use_pixel_counts, 
                **thematic_band_statistics_combined, 
                **point_stats})

            # If this is the first row...
            if aggregated_df.empty:
                # Initiate Pandas DataFrame
                aggregated_df = pd.DataFrame([combined])
            else:
                aggregated_df = aggregated_df.append(combined, ignore_index=True)

    # Create name to output
    aggregated_df.to_csv(args.output, float_format = '%.2f')

if __name__ == '__main__':
    main()