import argparse
import os

import pandas as pd

from shapely.geometry import Point, point
from geopandas import GeoDataFrame

from tqdm import tqdm

import rasterio as rio
from osgeo import gdal

from sample.data_analysis import calculate_raster_statistics, count_pixels_in_raster
from sample.helpers import read_band_names
from sample.pitfall import calculate_point_statistics_from_raster

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description = 'This command converts the tiles into a usable dataset.')

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
        default="output/data.csv"
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

    # Create columns for dataframe
    col_names = read_band_names(args.band_names)
          
    # Create an empty dataframe
    aggregated_df = pd.DataFrame()

    # Add column for ID
    #aggregated_df['ID'] = None

    # For each tile:
    ## Get the land use pixel proportions, and;
    ## Get the statistics of the thematic variables.

    # Loop through all tiles in folder
    tile_fnames = os.listdir(args.tiles)

    for tile_no in tqdm(range(len(tile_fnames)), desc = "Processing tiles..."):
        print("TILE NO: {}".format(tile_no))
        # Join path of folder and tile filename
        f = os.path.join(args.tiles, tile_fnames[tile_no])

        # Check if .tif file exists
        if os.path.isfile(f) and os.path.splitext(f)[1] == '.tif':
            # Read tile
            tile = rio.open(f)

            # Get land use proportions
            land_use_pixel_counts = count_pixels_in_raster(f, lut_fpath = args.lookup_table, band_no = 1)

            land_use_pixel_counts_series = pd.Series(land_use_pixel_counts)

            # Create combined dictionary for all thematic band statistics
            combined_dict = {}

            # Loop through all the thematic variables
            for band in range(2, tile.count + 1):
                thematic_var_statistics = calculate_raster_statistics(f, band)
                combined_dict = {**combined_dict, **thematic_var_statistics}

            combined_dict_series = pd.Series(combined_dict)

            # Adding point data            
            point_stats = calculate_point_statistics_from_raster(
                raster_fpath = f,
                point_csv_fpath = 'data/raw/pitfall_TER.csv'
            )

            # Adding ID row
            identifier = {
                'ID': int(tile_no) + 1
            }

            print()
            
            # Combine data (land use and thematic) in single row and convert to Pandas Series
            combined = pd.Series({**identifier, **land_use_pixel_counts, **combined_dict, **point_stats}, name=f)

            # series_list = [
            #     land_use_pixel_counts_series,
            #     combined_dict_series,
            #     point_stats_series
            # ]

            # combined = pd.concat(series_list)
            #print(combined)

            # If this is the first row...
            if aggregated_df.empty:
                # Initiate Pandas DataFrame
                aggregated_df = pd.DataFrame([combined])
            else:
                aggregated_df = aggregated_df.append(combined, ignore_index=False)

            aggregated_df

    aggregated_df.to_csv("output/results.csv", float_format = '%.2f')

if __name__ == '__main__':
    main()