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
    available_statistics = ['mean', 'min', 'max', 'median']
    
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
        raster.bounds[0]:raster.bounds[2], 
        raster.bounds[3]:raster.bounds[1]
    ]

    # Create empty dictionary from statistic values
    statistic_values = {}

    if points_within_raster.empty:
        return statistic_values

    # Select biodiversity indices (starting with: 'site_div')
    points_diversity_indices = points_within_raster.filter(regex='site_div*', axis=1)

    # Add statistics to list:
    ## MEAN
    if 'mean' in statistics:
        statistic_values.update(points_diversity_indices.mean().add_prefix("mean_"))

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
