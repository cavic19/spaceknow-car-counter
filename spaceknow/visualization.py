import math
from typing import Tuple
from geojson import Polygon
from PIL import Image
from PIL import ImageDraw

def tile_to_deg_coords(x_tile, y_tile, zoom) -> float:
    """Transforms presented tile coordinate to latitude, longitude degrees.

    Args:
        x_tile ([type])
        y_tile ([type])
        zoom ([type])

    Returns:
        (float, float): Latitude, longitude degrees.
    """
    n = 2.0 ** zoom
    lon_deg = x_tile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y_tile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)


def deg_to_tile_coords(lon_deg, lat_deg, zoom):
    """In acordance with presented zoom parametr, transforms latitudial, longitudial coordinates to tile coordinates

    Args:
        lat_deg (float): Latitudial degree
        lon_deg (float): Longitudial degree
        zoom (float): Zoom of final tile

    Returns:
        (float, float): (x_tile, y_tile)
    """
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x_tile = (lon_deg + 180.0) / 360.0 * n
    y_tile = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    return (x_tile, y_tile)


def highlight_cars_on_tile(tile: tuple[int,int,int], tile_image: Image.Image, car_features: list[Polygon], fill_color: str = "Red") -> Image.Image:
    """Highlights cars in given tile (given image) and returns the result.

    Args:
        tile (tuple[int,int,int]): Geographical boundaries of concern. 
        tile_image (Image.Image): Coresponds to a given tile.
        car_features (list[Polygon]): Each polygon represents area taken up by a car. Coordinates are expressed in longitudial, latitudial cooridnates.
        fill_color (str, optional): Highlighting color. Defaults to "Red".

    Returns:
        Image.Image
    """
    # "polygon['coordinates']" are represented by [[[lon_deg0, lat_deg0], [lon_deg1, lat_deg1], ...]]
    highlight_coords_tuples = [[tuple(coords) for coords in polygon['coordinates'][0]] for polygon in car_features]
    highlight_tile_coords = [[deg_to_tile_coords(*coords, tile[0]) for coords in coords_list] for coords_list in highlight_coords_tuples]
    highlight_pixel_coords = [[tile_to_pixel_coords((tile[1], tile[2]), tile_image.size, coords ) for coords in coords_list] for coords_list in highlight_tile_coords]
    
    draw = ImageDraw.Draw(tile_image)
    for polygon_coords in highlight_pixel_coords:
        draw.polygon(polygon_coords,fill=fill_color)
    return tile_image


def tile_to_pixel_coords(origin: Tuple[int,int], image_size: Tuple[int,int], abs_coords: Tuple[int,int]) -> Tuple[int, int]:
    """Transforms absolute geographical tile coordinates to pixel coordinates relative to the origin.

    Args:
        origin (Tuple[int,int])
        image_size (Tuple[int,int])
        abs_coords (Tuple[int,int])

    Returns:
        (int, int): Relative pixel coordinates
    """
    width = image_size[0]
    height = image_size[1]

    x = (abs_coords[0] - origin[0]) * width
    y = (abs_coords[1] - origin[1]) * height 

    return (x, y)



def merge_images(images: list[list[Image.Image]]) -> Image.Image:
    """Merge images in give layout to a one image.

    Args:
        images (list[list[Image.Image]]): Images if desired layout.

    Returns:
        Image.Image
    """ 
    horizontally_merged_images = []
    for hor_images in images:
       horizontally_merged_images.append(__merge_horizontally(hor_images))
    return __merge_vertically(horizontally_merged_images)

def __merge_horizontally(images: list[Image.Image]) -> Image.Image:
    widths, heights = zip(*[i.size for i in images])
    total_width = sum(widths)
    total_height = max(heights)

    new_im = Image.new('RGB', (total_width,total_height))
    x_offset = 0
    for im in images:
        new_im.paste(im,(x_offset,0))
        x_offset += im.size[0]
    return new_im

def __merge_vertically(images: list[Image.Image]) -> Image.Image:
    widths, heights = zip(*[i.size for i in images])   
    total_width = max(widths)
    total_height = sum(heights)
    
    new_im = Image.new('RGB', (total_width, total_height))
    y_offset = 0
    for im in images:
        new_im.paste(im,(0,y_offset))
        y_offset += im.size[1]
    return new_im

    