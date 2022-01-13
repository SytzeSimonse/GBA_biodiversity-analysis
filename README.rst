Introduction
===============
This script was written in fullfillment of my master internship at the *Grupo da Biodiversidade* (Biodiversity Group) 
of the University of the Azores (UAc). The script is licensed under the . (see License).

How to install
===============
This script uses the `setup.py` library for installing the package. Simply run the following command:
`pip install -e .`

How to use
===============

This script is intended to be used for tiling multiband raster data. Requirements:

* The first band is for landuse;
* The other bands are thematic rasters (e.g. climatic variables).

The package offers four commands you can use:

* ``aggregate``
* ``name-bands``
* ``spectral-heterogeneity``
* ``create-polygon``

In the subsection below, the usage of each command is explained. 
You can also always run `--help` for any of the commands.

Aggregate 
---------------
The aggregate command is used to aggregate raster data by tiles. 
The command requires as input a raster with a least two bands; one of which should contain a land use classification.
In addition, the position of the land use band in the order of raster bands should be provided.  
Furthermore, a look-up table (LUT) with the land use classes should be provided as a TXT file. 
The format of the LUT should be as follows (example):

::

    0=clouds
    1=urban
    2=bare_soil
    3=other_crops
    4=trees
    ...

::

The dimensions to aggregate the data over can also be specified, and should be provided as a list of integers.
For each dimension, a CSV file is created and stored in the specified folder.

Folder structure
===============
This is the folder structure

::

    - data/
        + intermediate/
        + raw/
    - docs/
    - figures/
    - output/
    - sample/
    - tests/
    - README.rst 
    - requirements.txt
    - setup.cfg
    - setup.py