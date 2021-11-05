from re import M, VERBOSE
import rasterio as rio
import numpy as np

import os

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

    pixel_counts = np.round(
        np.true_divide(pixel_counts[1:], non_zero_pixels),
        2)

    # Create dictionary for land use names and proportions
    pixel_count_dict = dict(zip(land_use_class_dict.values(), pixel_counts))

    return pixel_count_dict

def calculate_raster_statistics(tile_fpath: str, band_no: int) -> list:
    # TESTS
    assert os.path.isfile(tile_fpath), "'{}' is not a file.".format(tile_fpath)
    
    # Opening tile
    try:
        tile = rio.open(tile_fpath)
    except FileNotFoundError:
        "The file {} cannot be found.".format(tile_fpath)

    # Reading band
    band = tile.read(band_no)

    # Set negative values to NaN
    band[band < 0] = np.nan

    # List of statistic names to include
    statistic_names = ['mean', 'minimum', 'maximum', 'range', 'median', 'coefficient_of_variation']

    # Add band number to statistics
    statistic_names = [("band {} - ".format(band_no) + stat) for stat in statistic_names]

    # List of statistic values (as calculated)
    # NOTE: These should be in the exact same order as the names.
    statistic_values = []

    statistic_values.append(
        round(np.nanmean(band), 2)
    )

    statistic_values.append(
        round(np.nanmin(band), 2)
    )

    statistic_values.append(
        round(np.nanmax(band), 2)
    )

    statistic_values.append(
        abs(statistic_values[2] - statistic_values[1])
    )

    statistic_values.append(
        round(np.nanmedian(band), 2)
    )

    statistic_values.append(
        round((statistic_values[1] / statistic_values[0]) * 100, 2)
    )

    # statistic_values.append(round(float(tile.tags(band_no)['STATISTICS_MEAN']), 2))
    # statistic_values.append(round(float(tile.tags(band_no)['STATISTICS_MINIMUM']), 1))
    # statistic_values.append(round(float(tile.tags(band_no)['STATISTICS_MAXIMUM']), 1))
    # statistic_values.append(abs(statistic_values[2] - statistic_values[1]))
    # statistic_values.append(np.median(band[band > statistic_values[1]]))
    # # SOURCE: https://www.statology.org/coefficient-of-variation-in-python/
    # statistic_values.append(round(float(tile.tags(band_no)['STATISTICS_MINIMUM']) / float(tile.tags(band_no)['STATISTICS_MEAN']) * 100, 2))  

    assert len(statistic_names) == len(statistic_values), "The number of calculated values should be equal to the number of included statistics."

    # Create dictionary for statistics
    statistics = dict(zip(statistic_names, statistic_values))

    return statistics