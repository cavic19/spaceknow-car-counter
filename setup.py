from setuptools import setup, find_packages

setup(
    name='spackenow-car-analyser',
    version='1.0',
    author='David Tomecek',
    author_email='david.tomecek1@seznam.cz',
    url='https://github.com/cavic19/spaceknow-car-counter',
    install_requires=['Pillow','geojson','requests'],
    packages=find_packages(exclude=['tests*']),
)