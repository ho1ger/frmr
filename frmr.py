#!/Users/hk/Pictures/out/venv_for_image_scripts/bin/python3

import sys
import os
from PIL import Image, ImageOps
import piexif
import configparser

# Reads the configuration from the config.ini file
def read_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    try:
        config.read(config_path)
        if not config.sections():
            sys.exit(1)  # Exit if no sections are found in the config
    except Exception as e:
        sys.exit(1)  # Exit on any exception during config reading
    
    return config

# Retrieves EXIF data from the given file
def get_exif(file):
    try:
        exif_dict = piexif.load(file)
        return exif_dict
    except Exception as e:
        return None  # Return None if EXIF data cannot be retrieved

# Generates a new filename based on the original file, extension, and type
def get_new_filename(file, extension, type):
    typeString = f"_{type}" if type != "" else ""
    return f"{file.rsplit('.', 1)[0]}{typeString}.{extension}"

# Saves the image with the specified quality and EXIF data if required
def store_image(img, file, config, type=""):
    quality = int(config['common']['quality'])
    export_exif = config.getboolean('common', 'export_exif')
    extension = config['common']['extension']
    new_file_name = get_new_filename(file, extension, type)
    
    try:
        img_to_save = img.convert('RGB')
        if extension.lower() == 'png':
            img_to_save.save(new_file_name)  # Save as PNG
        else:
            if export_exif:
                exif_dict = get_exif(file)
                img_to_save.save(new_file_name, quality=quality, exif=piexif.dump(exif_dict))  # Save with EXIF
            else:
                img_to_save.save(new_file_name, quality=quality)  # Save without EXIF
    except Exception as e:
        pass  # Ignore any exceptions during image saving

# Loads an image file and converts it to the specified mode
def load_image(file, mode='RGBA'):
    with Image.open(file) as img:
        return img.convert(mode)

# Adds a border to the image and saves it
def border(file, config):
    img = load_image(file, 'RGBA')
    img = ImageOps.expand(img, border=1, fill='black')  # Add black border
    img = ImageOps.expand(img, (40, 40), fill='white')  # Add white border
    store_image(img, file, config)  # Save the modified image

# Resizes the image to fit Instagram frame dimensions and saves it
def instaFrame(file, config):
    image = load_image(file, 'RGBA')
    img_w, img_h = image.size
    aspect_ratio = img_w / img_h
    if aspect_ratio > 1080 / 1350:
        new_w = 1080
        new_h = int(new_w / aspect_ratio)
    else:
        new_h = 1350
        new_w = int(new_h * aspect_ratio)
    image = image.resize((new_w, new_h), Image.LANCZOS)  # Resize image
    new_img = Image.new(mode="RGB", size=(1080, 1350), color="white")  # Create new white background
    bg_w, bg_h = new_img.size
    offset = ((bg_w - new_w) // 2, (bg_h - new_h) // 2)  # Calculate offset for centering
    new_img.paste(image, offset)  # Paste resized image onto background
    store_image(new_img, file, config, "insta")  # Save the framed image

# Adds letterbox effect to the image and saves it
def letterbox(file, config):
    img = load_image(file, 'RGB')
    original_width, original_height = img.size
    format_ratio = config['letterbox']['format'].split(':')
    aspect_ratio_width = int(format_ratio[0])
    aspect_ratio_height = int(format_ratio[1])
    new_height = int(original_width * aspect_ratio_height / aspect_ratio_width)
    new_img = Image.new("RGB", (original_width, new_height), (0, 0, 0))  # Create new black background
    y_offset = (new_height - original_height) // 2  # Calculate vertical offset
    new_img.paste(img, (0, y_offset))  # Paste original image onto background
    store_image(new_img, file, config)  # Save the letterboxed image

# Processes the image based on its aspect ratio and configuration
def process_image(file, config):
    with Image.open(file) as img:
        original_width, original_height = img.size
        aspect_ratio = original_width / original_height
        if abs(aspect_ratio - 2.35) < 0.01:
            letterbox(file, config)  # Apply letterbox if aspect ratio matches
        else:
            border(file, config)  # Otherwise, apply border
            if config.getboolean('common', 'insta'):
                instaFrame(file, config)  # Apply Instagram frame if enabled

# Main execution block
if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(1)  # Exit if no files are provided
    config = read_config()  # Read configuration
    for file in sys.argv[1:]:
        try:
            process_image(file, config)  # Process each provided image file
        except Exception as e:
            pass  # Ignore any exceptions during processing
