import os
import argparse

import rasterio as rio
from matplotlib import pyplot as plt

import pandas as pd

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description = 'This command displays the tile.')

    ## INPUT
    parser.add_argument('-t', '--tile',
        type = str,
        help='Filepath of tile'
    )

    ## DATA
    parser.add_argument('-c', '--csv',
        type = str,
        help='Filepath of CSV file with additional data',
        default='output/tiles_2000_result.csv'
    )

    args = parser.parse_args()

    # Open raster
    tile = rio.open(args.tile)

    # Add band 1 to plot
    plt.imshow(tile.read(1), cmap='viridis_r')

    # Set title
    plt.title("File '{}'".format(args.tile))

    # Selecting associated data from CSV
    df = pd.read_csv(args.csv)
    result = df.loc[df['filename'] == args.tile]

    # Show plot
    plt.show()

if __name__ == '__main__':
    main()