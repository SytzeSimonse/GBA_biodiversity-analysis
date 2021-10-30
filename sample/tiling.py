import os

import argparse

import rasterio as rio

from sample.raster import add_padding_to_raster, tile_raster, delete_single_value_tiles

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description = 'This script converts a raster into a usable dataset.')

    ## INPUT
    parser.add_argument('-r', '--raster',
        type = str,
        help='Filepath of raster'
    )

    ## OUTPUT
    parser.add_argument('-o', '--output',
        type = str,
        help='Folder of tiles',
        default="data/intermediate/raster.tif"
    )

    ## TILE DIMENSION
    parser.add_argument('-d', '--dimension',
        type=int,
        help='Dimension of tile'
    )

    ## VERBOSITY
    parser.add_argument('-v', '--verbose',
        help='Verbose output'
    )
    args = parser.parse_args()

    padded_raster_filepath = "data/intermediate/padded_raster.tif"

    # Add padding to raster
    add_padding_to_raster(
        raster_in = args.raster,
        raster_out = padded_raster_filepath,
        dimension = args.dimension
        )

    # Tile raster
    tile_raster(
        raster_in = padded_raster_filepath,
        raster_out = "data/intermediate/tiles",
        dimension = args.dimension,
        verbose = args.verbose
    )

    # Delete single-value rasters
    delete_single_value_tiles(
        tiles_folder = "data/intermediate/tiles"
    )

if __name__ == '__main__':
    main()