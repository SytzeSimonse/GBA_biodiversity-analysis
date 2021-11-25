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
        statistics (list): Statistics to include. Choose from: mean, min, max, median. Default: ['mean'].
    Returns:
        dict: Statistic names and values
    """
    # List of possible statistics
    available_statistics = ['mean', 'minimum', 'maximum', 'median']
    
    # Check if any statistic is used that is not available
    for statistic in statistics:
        assert statistic in available_statistics, "'{}' is not an available option.".format(statistic)

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
        ## left, right
        ## top, bottom
        raster.bounds[0]:raster.bounds[2], 
        raster.bounds[3]:raster.bounds[1]
    ]

    # Create empty dictionary from statistic values
    statistic_values = {}

    if points_within_raster.empty:
        return statistic_values

    # Add statistics to list:
    ## MEAN
    if 'mean' in statistics:
        statistic_values.update(points_within_raster.iloc[:,30:-1].mean().add_prefix("mean_"))

    ## MEDIAN
    if 'median' in statistics:
        statistic_values.update(points_within_raster.iloc[:,-29:].median().add_prefix("median_"))

    ## MINIMUM
    if 'minimum' in statistics:
        statistic_values.update(points_within_raster.iloc[:,-29:].min().add_prefix("min_"))

    ## MAXIMUM
    if 'maximum' in statistics:
        statistic_values.update(points_within_raster.iloc[:,-29:].max().add_prefix("max_"))

    return statistic_values

def calculate_point_statistics_from_raster_v2(
    bounding_box: list,
    point_csv_fpath: str, 
    statistics: list = ['mean']
    ) -> dict:
    """Calculates statistics of points found within a raster.

    Args:
        raster_fpath (str): Filepath to raster
        point_csv_fpath (str): Filepath to CSV with point data
        statistics (list): Statistics to include. Choose from: mean, min, max, median. Default: ['mean'].
    Returns:
        dict: Statistic names and values
    """
    # List of possible statistics
    available_statistics = ['mean', 'minimum', 'maximum', 'median']
    
    # Check if any statistic is used that is not available
    for statistic in statistics:
        assert statistic in available_statistics, "'{}' is not an available option.".format(statistic)

    # Read point data as Pandas DataFrame
    df = pd.read_csv(point_csv_fpath)

    # Get geometry from DataFrame
    geometry = [Point(xy) for xy in zip(df['UTM E'], df['UTM N'])]

    # Create GeoPandas DataFrame, using geometries
    gdf = GeoDataFrame(df, geometry = geometry)

    #Create list of points found within raster
    points_within_raster = gdf.cx[
        ## NOTE: bounds = left, bottom, right, top
        bounding_box[0]:bounding_box[1], 
        bounding_box[2]:bounding_box[3]
    ]

    # Create empty dictionary from statistic values
    statistic_values = {}

    if points_within_raster.empty:
        return statistic_values, 0

    # Add statistics to list:
    ## MEAN
    if 'mean' in statistics:
        mean_of_points = points_within_raster.iloc[:,30:-1].mean().add_prefix("mean_")
        statistic_values.update(round(mean_of_points, 2))

    ## MEDIAN
    if 'median' in statistics:
        statistic_values.update(points_within_raster.iloc[:,-29:].median().add_prefix("median_"))

    ## MINIMUM
    if 'minimum' in statistics:
        statistic_values.update(points_within_raster.iloc[:,-29:].min().add_prefix("min_"))

    ## MAXIMUM
    if 'maximum' in statistics:
        statistic_values.update(points_within_raster.iloc[:,-29:].max().add_prefix("max_"))

    print("Statistics: {}".format(statistics))
    print("Len: {}".format(len(points_within_raster)))

    return statistic_values, len(points_within_raster)
