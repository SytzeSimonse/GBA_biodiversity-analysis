import os
import re

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

# Sorting function
## FROM: https://stackoverflow.com/questions/4813061/non-alphanumeric-list-order-from-os-listdir/48030307#48030307
def sort_alphanumerically(data: list) -> list:
    """Sorts a list alphanumerically.   

    Args:
        data (list): List of items.

    Returns:
        list: List of alphanumerically sorted items.
    """
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(data, key=alphanum_key)
