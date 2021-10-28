import math
from typing import Tuple
from geojson import Polygon
from PIL import Image
from PIL import ImageDraw

def tile_to_deg(x, y, z):
    """Converts tile (x, y, z) to longitudial, latitudial coordinates."""
    n = 2.0 ** z
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def deg_to_tile(lat_deg, lon_deg, z):
    """Converts tile (x, y, z) to longitudial, latitudial coordinates."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** z
    xtile = (lon_deg + 180.0) / 360.0 * n
    ytile = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    return (xtile, ytile)


def create_image_from_tile(tile: tuple[int,int,int], bc_image: Image.Image, highlights: list[Polygon], fill_color: str = None):
    highlight_coords_tuples = [[tuple(j[::-1]) for j in i['coordinates'][0]] for i in highlights]
    highlight_tile_coords = [[deg_to_tile(*j, tile[0]) for j in i] for i in highlight_coords_tuples]
    highlight_pixel_coords = [[__map_to_pixel_coordinates((tile[1], tile[2]), bc_image.size, j ) for j in i] for i in highlight_tile_coords]
    
    draw = ImageDraw.Draw(bc_image)
    for polygon_coords in highlight_pixel_coords:
        draw.polygon(polygon_coords,fill=fill_color or "red")
    return bc_image


def __map_to_pixel_coordinates(origin: Tuple[int,int], image_size: Tuple[int,int], abs_coords: Tuple[int,int]):
    width = image_size[0]
    height = image_size[1]

    x = (abs_coords[0] - origin[0]) * width
    y = (abs_coords[1] - origin[1]) * height 

    return (x, y)

def merge_images(images: list[list[Image.Image]]) -> Image.Image:
    """Merges images in acordance with a given layout. Outputs final image."""
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

    