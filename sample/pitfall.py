from os import stat
import rasterio as rio

import pandas as pd

from shapely.geometry import Point
from geopandas import GeoDataFrame

def calculate_point_statistics_within_bounds(
    bounding_box: list,
    point_csv_fpath: str, 
    statistics: list = ['mean'],
    verbose: bool = True
    ) -> dict:
    """Aggregates the values of point data found within specified bounds into statistics.

    Args:
        bounding_box (list): Bounding box with 4 values (X1, Y1, X2, Y2).
        point_csv_fpath (str): Filepath to CSV file with point data.
        statistics (list, optional): List of statistics to return. Defaults to ['mean'].
        verbose (bool, optional): Verbosity flag.

    Returns:
        dict: [description]
    """
    assert len(bounding_box) == 4, "The bounding box should be specified with 4 values; not {}.".format(len(bounding_box))


    # Create list of available statistics
    available_statistics = ['mean', 'minimum', 'maximum', 'median']
    
    # Check if any statistic is specified that is not available
    for statistic in statistics:
        assert statistic in available_statistics, "'{}' is not an available option.".format(statistic)

    # Read point data as Pandas DataFrame
    df = pd.read_csv(point_csv_fpath)

    # Get geometry from DataFrame
    geometry = [Point(xy) for xy in zip(df['UTM E'], df['UTM N'])]

    # Create GeoPandas DataFrame, using geometries
    gdf = GeoDataFrame(df, geometry = geometry)

    #Create list of points found within raster
    points_within_bounds = gdf.cx[
        bounding_box[0]:bounding_box[1], 
        bounding_box[2]:bounding_box[3]
    ]

    # Create empty dictionary from statistic values
    statistic_values = {}

    # If no points are found, return empty dictionary
    if points_within_bounds.empty:
        return statistic_values
    
    # Add the number of points found within the bounds to dictionary with statistics
    statistic_values.update({"number of points": len(points_within_bounds)})

    # Add statistics to list:
    ## MEAN
    if 'mean' in statistics:
        mean_of_points = points_within_bounds.iloc[:,30:-1].mean().add_prefix("mean_")
        statistic_values.update(round(mean_of_points, 2))

    ## MEDIAN
    if 'median' in statistics:
        statistic_values.update(points_within_bounds.iloc[:,-29:].median().add_prefix("median_"))

    ## MINIMUM
    if 'minimum' in statistics:
        statistic_values.update(points_within_bounds.iloc[:,-29:].min().add_prefix("min_"))

    ## MAXIMUM
    if 'maximum' in statistics:
        statistic_values.update(points_within_bounds.iloc[:,-29:].max().add_prefix("max_"))

    if verbose:
        print("Within this bound, there are {} points.".format(len(points_within_bounds)))

    return statistic_values
