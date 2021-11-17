import argparse

from sample.raster import set_band_descriptions

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description = 'This command assigns names to the raster bands.')

    ## INPUT
    parser.add_argument('-r', '--raster',
        type = str,
        help='Filepath of raster',
        default='data/raw/combined.tif'
    )

    ## BAND NAMES
    parser.add_argument('-n', '--names',
        type = str,
        help='Filepath of .txt file with band names (each row represents a name)',
        default="data/raw/bands.txt"
    )

    ## VERBOSITY
    parser.add_argument('-v', '--verbose',
        help='Verbose output',
        default=True
    )

    args = parser.parse_args()

    print(args.raster)
    print(args.names)

    set_band_descriptions(
        raster_fpath = args.raster,
        bands_txt = args.names
    )