import os

import argparse

import rasterio as rio

from sample.helpers import find_landuse_classes
from sample.raster import add_padding_to_raster, determine_padding, tile_raster

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

    # Add padding to raster
    add_padding_to_raster(
        raster_in = args.raster,
        raster_out = "data/intermediate/raster.tif",
        dimension = args.dimension
        )

    # Tile raster
    # tile_raster(args.raster, args.output, args.dimension, verbose = args.verbose)

if __name__ == '__main__':
    main()