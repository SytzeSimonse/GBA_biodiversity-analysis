from os import stat
import rasterio as rio

import pandas as pd

from shapely.geometry import Point
from geopandas import GeoDataFrame

def calculate_point_statistics_from_raster(
    raster_fpath: str, 
    point_csv_fpath: str, 
    statistics: list = ['mean']
    ) -> dict:
    """Calculates statistics of points found within a raster.

    Args:
        raster_fpath (str): Filepath to raster
        point_csv_fpath (str): Filepath to CSV with point data
        statistics (list):
    Returns:
        dict: Statistic names and values
    """
    # Open tile
    raster = rio.open(raster_fpath)

    # Read point data as Pandas DataFrame
    df = pd.read_csv(point_csv_fpath)

    # Get geometry from DataFrame
    geometry = [Point(xy) for xy in zip(df['UTM E'], df['UTM N'])]

    # Create GeoPandas DataFrame, using geometries
    gdf = GeoDataFrame(df, geometry = geometry)

    # Create list of points found within raster
    points_within_raster = gdf.cx[
        ## NOTE: bounds = left, bottom, right, top
        raster.bounds[0]:raster.bounds[2], 
        raster.bounds[3]:raster.bounds[1]
    ]

    # Create empty dictionary from statistic values
    statistic_values = {}

    # List of possible statistics
    available_statistics = ['mean', 'min', 'max', 'median', 'range']
    
    # ASSERTIONS
    for statistic in statistics:
        assert statistic in available_statistics, "'{}' is not an available option.".format(statistic)
    
    # Add statistics to list:
    ## MEAN
    if 'mean' in statistics:
        statistics['mean'] = points_within_raster.iloc[:,-29:].mean()

    ## MEDIAN
    if 'median' in statistics:
        statistics['median'] = points_within_raster.iloc[:,-29:].median()

    return statistic_values
