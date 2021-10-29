import rasterio as rio
import numpy as np

def count_pixels_in_raster(tile_fname: str, band_no: int = 1):
    # Opening tile
    tile = rio.open(tile_fname) 

    tile_selected_band = rio.

    # Calculate the total tile size
    tile_total_size = tile.shape[0] ** 2

    # Count the pixels
    pixel_counts = np.bincount(tile.flatten(), minlength = len(land_use_class_dict) + 1)

    non_zero_pixels = tile_total_size - pixel_counts[0]

    pixel_counts = np.round(
        np.true_divide(pixel_counts[1:], non_zero_pixels),
        2)

    if np.sum(pixel_counts) > 1:
        print(pixel_counts[1:])

    return pixel_counts