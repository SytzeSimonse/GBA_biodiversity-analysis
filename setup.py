from setuptools import setup, find_packages

setup(
    name='example',
    version='0.1.0',
    packages=find_packages(include=['sample', 'sample.*']),
    install_requires=[
        'numpy',
        'rasterio',
        'geopandas',
        'pandas'
    ],
    entry_points={
        'console_scripts': [
            'snek = sample.example:main'
            ],
    },
    setup_requires=[
        'pytest-runner'
        ],
    tests_require=['pytest'],
)