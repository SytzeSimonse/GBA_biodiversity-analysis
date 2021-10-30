from re import VERBOSE
import rasterio as rio
import numpy as np

from rasterio.plot import show

from sample.helpers import read_land_use_classes

def count_pixels_in_raster(tile_fpath: str, lut_fpath: str, band_no: int = 1) -> list:
    """Counts the pixel proportions (summing to 1) of a raster.

    Args:
        tile_fpath (str): Filepath of tile (.tif).
        lut_fpath (str): Filepath of LookUp-Table (.txt).
        band_no (int, optional): Band number to use. Defaults to 1.

    Returns:
        list: Proportions of land use classes.
    """
    # Opening tile
    tile = rio.open(tile_fpath) 

    # Reading band
    band = tile.read(band_no)

    # Calculate the total tile size
    ## NOTE: The tile should be square-sized, but to be sure the height is multiplied by the width.
    tile_total_size = tile.shape[0] * tile.shape[1]

    # Get landuse classes
    land_use_class_dict = read_land_use_classes(lut_fpath)

    # Count the pixels
    pixel_counts = np.bincount(band.flatten().astype(np.int32), minlength = len(land_use_class_dict) + 1)

    # Calculate the pixels which do not have zero (= NoData/cloud) pixels
    non_zero_pixels = tile_total_size - pixel_counts[0]

    print("\n")
    print(pixel_counts)

    pixel_counts = np.round(
        np.true_divide(pixel_counts[1:], non_zero_pixels),
        2)

    return pixel_counts

def calculate_raster_statistics(tile_fpath: str, band_no: int) -> list:
    # Opening tile
    tile = rio.open(tile_fpath) 

    # Reading band
    band = tile.read(band_no)

    show(band)

    return

    # List of statistics to include
    stats_list = ['mean', 'median', 'range', 'maximum', 'minimum', 'coefficient_of_variation']

    # Create a dictionary for statistics with no values
    stats = {
        key: 0 for key in stats_list
    }

    # Calculate statistics (using NumPy)
    print(band)
    stats['mean'] = np.average(band)
    stats['median'] = np.median(band)
    stats['range'] = abs(np.max(band) - np.min(band)) # TODO: Direct function?
    stats['maximum'] = np.max(band)
    stats['minimum'] = np.min(band)

    # Define function to calculate cv
    #   SOURCE: https://www.statology.org/coefficient-of-variation-in-python/
    cv = lambda x: np.std(x, ddof=1) / np.mean(x) * 100  

    #stats['coefficient_of_variation'] = cv(band)

    return stats
