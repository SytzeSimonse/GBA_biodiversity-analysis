import os

def read_land_use_classes(lut_fpath) -> dict:
    """Finds a .txt file in the data folder to extract landuse classes from.

    Raises:
        FileNotFoundError: if file called 'classes.txt' is not found in data folder.

    Returns:
        dict: land use number (key) and name (value) pairs.
    """
    if os.path.exists(lut_fpath):
        # Create emptydictionary for landuse classes
        landuse_class_dict = {}

        # Read .txt file
        with open(lut_fpath) as f:
            lines = f.read().splitlines()
            print("You have {} landuse classes.".format(len(lines)))

            # Loop through lines
            for line in lines:
                landuse_class = line.split('=')[0]
                landuse_name = line.split('=')[1]
                landuse_class_dict[landuse_class] = landuse_name

        return landuse_class_dict
    else:
        raise FileNotFoundError(
            "You need a .txt file with the land use classes."
        )

def read_band_names(band_names_fpath: str) -> list:
    if os.path.exists(band_names_fpath):
        # Create empty list for band names
        band_names = []

        # Read .txt file
        with open(band_names_fpath) as f:
            lines = f.read().splitlines()
            print("You have {} band names.".format(len(lines)))

            # Loop through lines
            for line in lines:
                band_names.append(line)

        return band_names
    else:
        raise FileNotFoundError(
            "You need a .txt file with the band names."
        )
