from PIL import Image

def merge_images(images: list[list[Image.Image]]) -> Image:
    """Merges images in acordance with a given layout. Outputs final image."""
    horizontally_merged_images = []
    for hor_images in images:
       horizontally_merged_images.append(__merge_horizontally(hor_images))
    return __merge_vertically(horizontally_merged_images)

def __merge_horizontally(images: list[Image.Image]) -> Image:
    widths, heights = zip(*[i.size for i in images])
    total_width = sum(widths)
    total_height = max(heights)

    new_im = Image.new('RGB', (total_width,total_height))
    x_offset = 0
    for im in images:
        new_im.paste(im,(x_offset,0))
        x_offset += im.size[0]
    return new_im

def __merge_vertically(images: list[Image.Image]) -> Image:
    widths, heights = zip(*[i.size for i in images])   
    total_width = max(widths)
    total_height = sum(heights)
    
    new_im = Image.new('RGB', (total_width, total_height))
    y_offset = 0
    for im in images:
        new_im.paste(im,(0,y_offset))
        y_offset += im.size[1]
    return new_im
