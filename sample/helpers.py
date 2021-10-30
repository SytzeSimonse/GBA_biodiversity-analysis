import os

def read_land_use_classes(lut_fpath) -> dict:
    """Finds a .txt file in the data folder to extract landuse classes from.

    Raises:
        FileNotFoundError: if file called 'classes.txt' is not found in data folder.

    Returns:
        dict: landuse class names.
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

