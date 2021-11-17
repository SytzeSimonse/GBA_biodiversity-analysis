import os

import numpy as np

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import rasterio as rio

def centeroidnp(arr):
    length = arr.shape[0]
    sum_x = np.sum(arr[:,0])
    sum_y = np.sum(arr[:,1])
    return sum_x/length, sum_y/length

def calculate_spectral_variance(raster_fpath):
    assert os.path.exists(raster_fpath), "The file '{}' does not exist.".format(raster_fpath)
    assert os.path.splitext(raster_fpath)[1] == ".tif", "The file should be in GeoTIFF format."

    # Open raster
    raster = rio.open(raster_fpath)

    # Read bands as NumPy array
    data = raster.read()

    # Reshape
    data_reshaped = np.reshape(data, (raster.count, data.shape[1] * data.shape[2]))

    # Standardizing the features
    data_reshaped = StandardScaler().fit_transform(data_reshaped)

    # Perform PCA
    pca = PCA(n_components = 2)

    # Store fitted PCA
    result = pca.fit(data_reshaped).components_

    # Calculate centroid
    centroid = centeroidnp(result)

    # Variable for summing distances
    total_distance = 0
    
    # Calculate the distance from each point to the centroid
    for i in range(0, result.shape[1]):
        distance = ((result[0,i] - result[1,i])**2 + (centroid[0] - centroid[1])**2)**0.5
        total_distance += distance

    # Return average value
    return total_distance / result.shape[1]
