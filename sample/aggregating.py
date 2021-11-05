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
    aggregated_df  = pd.DataFrame()

    # For each tile:
    ## Get the land use pixel proportions, and;
    ## Get the statistics of the thematic variables.

    # Loop through all tiles in folder
    for tile in tqdm(os.listdir(args.tiles)):
        f = os.path.join(args.tiles, tile)
        if os.path.isfile(f):
            print("Currently processing '{}'...".format(f))

            # Read tile
            tile = rio.open(f)

            # Get land use proportions
            land_use_pixel_counts = count_pixels_in_raster(f, lut_fpath = args.lookup_table, band_no = 1)

            # Create combined dictionary for all thematic band statistics
            combined_dict = {}

            # Loop through all the thematic variables
            for band in range(2, tile.count + 1):
                thematic_var_statistics = calculate_raster_statistics(f, band)
                combined_dict = {**combined_dict, **thematic_var_statistics}

            # Adding point data            
            point_stats = calculate_point_statistics_from_raster(
                raster_fpath = f,
                point_csv_fpath = 'data/raw/pitfall_TER.csv'
            )

            # Combine data (land use and thematic) in single row and convert to Pandas Series
            combined = pd.Series({**land_use_pixel_counts, **combined_dict, **point_stats}, name=f)

            # If this is the first row...
            if aggregated_df.empty:
                # Initiate Pandas DataFrame
                aggregated_df = pd.DataFrame([combined])
            else:
                aggregated_df = aggregated_df.append(combined)

            aggregated_df

    aggregated_df.to_csv("output/results.csv", float_format = '%.2f')

if __name__ == '__main__':
    main()