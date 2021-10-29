import os

def find_landuse_classes() -> dict:
    """Finds a .txt file in the data folder to extract landuse classes from.

    Raises:
        FileNotFoundError: if file called 'classes.txt' is not found in data folder.

    Returns:
        dict: landuse class names.
    """
    # Find .txt file with landuse classes
    classes_file = 'data/raw/classes.txt'

    if os.path.exists(classes_file):
        # Create emptydictionary for landuse classes
        landuse_class_dict = {}

        # Read .txt file
        with open(classes_file) as f:
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

