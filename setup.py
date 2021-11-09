from setuptools import setup, find_packages

setup(
    name='UAc_GBA_Project',
    version='0.1.0',
    packages=find_packages(include=['sample', 'sample.*']),
    install_requires=[
        'numpy',
        'rasterio',
        'geopandas',
        'pandas',
        'rasterstats',
        'matplotlib',
        'gdal'
    ],
    entry_points={
        'console_scripts': [
            'tile = sample.tiling:main',
            'aggregate = sample.aggregating:main',
            'name_bands = sample.naming_bands:main',
            'visualise-tile = sample.visualise:main'
            ],
    },
    setup_requires=[
        'pytest-runner'
        ],
    tests_require=['pytest'],
)