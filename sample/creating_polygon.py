import argparse
import os
import pandas as pd

from shapely.geometry import mapping, Polygon
import fiona

def main():
    parser = argparse.ArgumentParser(
        description = """This command creates a polygon using the extent coordinates from a CSV file."""
    )

    ## INPUT
    parser.add_argument('-d', '--data',
        type = str,
        help = 'Filepath to data (CSV)'
    )

    ## INPUT
    parser.add_argument('-idx', '--index',
        type = int,
        help = 'Index of row of the CSV file.',
        default = 2
    )

    ## OUTPUT
    parser.add_argument('-o', '--output',
        type = str,
        help = 'Folder of GeoShape Package',
        default="output/polygons.shp"
    )

    args = parser.parse_args()

    data_table = pd.read_csv(args.data)

    left = data_table.iloc[args.index:,]["left"].values[0]
    right = data_table.iloc[args.index:,]["right"].values[0]
    top = data_table.iloc[args.index:,]["top"].values[0]
    bottom = data_table.iloc[args.index:,]["bottom"].values[0]

    p1 = [left, top]
    p2 = [right, top]
    p3 = [right, bottom]
    p4 = [left, bottom]

    # Here's an example Shapely geometry
    poly = Polygon([p1, p2, p3, p4])

    # Here's an example Shapely geometry
    # Define a polygon feature geometry with one attribute
    schema = {
        'geometry': 'Polygon',
        'properties': {'id': 'int'},
    }

    # Write a new Shapefile
    with fiona.open('output/my_shp2.shp', 'w', 'ESRI Shapefile', schema) as c:
        ## If there are multiple geometries, put the "for" loop here
        c.write({
            'geometry': mapping(poly),
            'properties': {'id': args.index},
        })

if __name__ == '__main__':
    main()