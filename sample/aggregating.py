import argparse
import os

import rasterio as rio

from sample.data_analysis import calculate_raster_statistics, count_pixels_in_raster

def main():
    print("Command has been called!")

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

    ## VERBOSITY
    parser.add_argument('-v', '--verbose',
        help='Verbose output',
        default=True
    )

    args = parser.parse_args()

    ## LAND USE ##
    # For each tile, get the land use pixel proportions
    for tile in os.listdir(args.tiles):
        f = os.path.join(args.tiles, tile)
        if os.path.isfile(f):
            # Show filename
            print(f)

            # Read tile
            tile = rio.open(f)

            # Get land use proportions
            land_use_pixel_counts = count_pixels_in_raster(f, lut_fpath = args.lookup_table, band_no = 1)
            print(land_use_pixel_counts)

            # Loop through all the thematic variables
            for band in range(2, tile.count + 1):
                print("Band no. {}".format(band))
                thematic_var_statistics = calculate_raster_statistics(f, band)
                print(thematic_var_statistics)

        break

    ## THEMATIC VARIABLES ##
            

if __name__ == '__main__':
    main()