import shutil

import click
import piexif
from PIL import Image

@click.group()
def cli():
    pass


@cli.command()
@click.argument("filenames", nargs=-1, required=True)
def fix(filenames):
    """Fix metadata for one or more files."""
    for filename in filenames:
        click.echo(f"Fixing metadata for: {filename}")
        img = Image.open(filename)
        w = img.width
        h = img.height

        exif_dict = piexif.load(filename)

        exif_dict["Exif"][piexif.ExifIFD.PixelXDimension] = w
        exif_dict["Exif"][piexif.ExifIFD.PixelYDimension] = h

        # Copy the original file to the new filename
        new_filename = filename.rsplit(".", 1)[0] + "_fixed.jpg"
        shutil.copy2(filename, new_filename)

        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, new_filename)

        click.echo(f"Fixed metadata for: {filename}, written to {new_filename}")

if __name__ == "__main__":
    cli()
