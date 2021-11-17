import os
import argparse
import re

import pandas as pd

from tqdm import tqdm

from sample.spectral import calculate_spectral_variance

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description = 'This script calculates the spectral heterogeneity for a set of tiles.')

    ## INPUT
    parser.add_argument('-t', '--tiles',
        type = str,
        help='Folder with tiles'
    )

    ## CSV
    parser.add_argument('-c', '--csv',
        type = str,
        help='Filepath to CSV of tiles',
        default='output/tile_dimension_1000.csv'
    )

    ## VERBOSITY
    parser.add_argument('-v', '--verbose',
        help = 'Verbose output',
        default = True
    )

    args = parser.parse_args()

    # Open CSV
    data = pd.read_csv(args.csv)

    # TODO: Refactor
    # Sorting function
    def sorted_alphanumeric(data):
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
        return sorted(data, key=alphanum_key)

    # Loop through all tiles in folder
    tile_fnames = sorted_alphanumeric(os.listdir(args.tiles))

    # Create list for spectral variances
    spectral_variances = pd.DataFrame(columns = ["filename", "spectral_variance"])

    for tile_no in tqdm(range(len(tile_fnames)), desc = "Processing tiles..."):
        # Join path of folder and tile filename
        f = os.path.join(args.tiles, tile_fnames[tile_no])

        # Check if .tif file exists
        if os.path.isfile(f) and os.path.splitext(f)[1] == '.tif':
            # Read tile
            spectral_variances = spectral_variances.append({
                'filename': f, 
                'spectral_variance': calculate_spectral_variance(f)
                }, ignore_index=True)

    # Add spectral variance values to DataFrame
    data = data.merge(spectral_variances, how='inner', on='filename')

    # Write result to CSV
    data.to_csv(args.csv)

if __name__ == '__main__':
    main()