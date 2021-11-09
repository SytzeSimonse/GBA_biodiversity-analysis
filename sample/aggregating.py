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
from sample.helpers import read_band_names
from sample.pitfall import calculate_point_statistics_from_raster

def main():
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
        default="output/default.csv"
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
    ## Get the statistics of the thematic variables.

    # Sorting function
    def sorted_alphanumeric(data):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
        return sorted(data, key=alphanum_key)

    # Loop through all tiles in folder
    tile_fnames = sorted_alphanumeric(os.listdir(args.tiles))

    for tile_no in tqdm(range(len(tile_fnames)), desc = "Processing tiles..."):
        # Join path of folder and tile filename
        f = os.path.join(args.tiles, tile_fnames[tile_no])

        # Check if .tif file exists
        if os.path.isfile(f) and os.path.splitext(f)[1] == '.tif':
            # Read tile
            tile = rio.open(f)

            # Get land use proportions (as dict)
            land_use_pixel_counts = count_pixels_in_raster(f, lut_fpath = args.lookup_table, band_no = 1)

            if land_use_pixel_counts['clouds/shadows'] == 1:
                continue

            # Create combined dictionary for all thematic band statistics
            thematic_band_statistics_combined = {}

            # Loop through all the thematic variables
            for band in range(2, tile.count + 1):
                # Calculate raster statistics for single band
                thematic_var_statistics = calculate_raster_statistics(f, band)

                if thematic_var_statistics == None:
                    continue

                # Add calculated raster statistics to combined dictionary
                thematic_band_statistics_combined = {**thematic_band_statistics_combined, **thematic_var_statistics}

            # Calculate statistics of point data (as dict)          
            point_stats = calculate_point_statistics_from_raster(
                raster_fpath = f,
                point_csv_fpath = 'data/raw/pitfall_TER.csv'
            )

            if not point_stats:
                print("Point stats: {}".format(point_stats))
                continue
            else:
                print(point_stats)

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
                **point_stats}, name=f)

            # If this is the first row...
            if aggregated_df.empty:
                # Initiate Pandas DataFrame
                aggregated_df = pd.DataFrame([combined])
            else:
                aggregated_df = aggregated_df.append(combined, ignore_index=False)

    # Create name to output
    aggregated_df.to_csv(args.output, float_format = '%.2f')

if __name__ == '__main__':
    main()