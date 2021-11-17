from re import M, VERBOSE
import rasterio as rio
import numpy as np

import os

from osgeo import gdal

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
    pixel_counts = np.bincount(band.flatten().astype(np.int32), minlength = len(land_use_class_dict))
    
    # Calculate proportion
    pixel_counts = np.round(
        np.true_divide(pixel_counts, tile_total_size),
        4)

    # Create dictionary for land use names and proportions
    pixel_count_dict = dict(zip(land_use_class_dict.values(), pixel_counts))

    return pixel_count_dict

def calculate_raster_statistics(
    tile_fpath: str, 
    band_no: int, 
    statistics: list = ['mean', 'range', 'coefficient_of_variation']
    ) -> list:    
    # Opening tile
    try:
        tile = rio.open(tile_fpath)
    except FileNotFoundError:
        "The file {} cannot be found.".format(tile_fpath)

    # # Loop through all bands
    # for band in range(1, len(bands)+1):
    #     rb = ds.GetRasterBand(band)
    #     rb.SetDescription(bands[band - 1])

    # dataset = gdal.Open(tile_fpath, gdal.GA_Update)
    # rb = dataset.GetRasterBand(band_no)
    # print(rb.GetDescription())

    # Reading band
    band = tile.read(band_no)

    # Set negative values to NaN
    band[band < 0] = np.nan

    # List of statistic names to include
    statistic_names = ['mean', 'minimum', 'maximum', 'range', 'median', 'coefficient_of_variation']

    # Add band number to statistics
    statistic_names = [("band {} - ".format(band_no) + stat) for stat in statistics]

    # List of statistic values (as calculated)
    # NOTE: These should be in the exact same order as the names.
    statistic_values = []

    # Check if band does not only contain NaN values
    if not np.isnan(band).all():
        # Mean  
        if 'mean' in statistics:
            statistic_values.append(
                round(np.nanmean(band), 3)
            )

        # Minimum
        if 'min' in statistics:
            statistic_values.append(
                round(np.nanmin(band), 3)
            )

        # Maximum
        if 'max' in statistics:
            statistic_values.append(
                round(np.nanmax(band), 3)
            )

        # Range
        if 'range' in statistics:
            statistic_values.append(
                round(np.nanmax(band) - np.nanmin(band), 3)
            )

        # Median
        if 'median' in statistics:
            statistic_values.append(
                round(np.nanmedian(band), 3)
            )

        # Coefficient of variation
        if 'coefficient_of_variation' in statistics:
            if not np.nanmean(band) == 0: # avoid division by zero
                statistic_values.append(
                    round((np.nanstd(band, ddof=1) / np.nanmean(band)) * 100, 3)
                )
    else:
        return None

    # Create dictionary for statistics
    statistics = dict(zip(statistic_names, statistic_values))

    return statistics