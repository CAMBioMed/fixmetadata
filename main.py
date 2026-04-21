import os
import shutil
from pathlib import Path

import click
import piexif
from PIL import Image

@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--output-dir",
    "-o",
    required=True,
    type=click.Path(file_okay=False, dir_okay=True, path_type=str),
    help="Directory where fixed files are written.",
)
@click.argument("filenames", nargs=-1, required=True)
def fix(output_dir, filenames):
    """Fix metadata for one or more files or directories."""
    os.makedirs(output_dir, exist_ok=True)

    def is_jpeg_file(path):
        return os.path.isfile(path) and Path(path).suffix.lower() in {".jpg", ".jpeg"}

    worklist = []
    for filename in filenames:
        if os.path.isdir(filename):
            worklist.extend(
                os.path.join(filename, f)
                for f in os.listdir(filename)
                if is_jpeg_file(os.path.join(filename, f))
            )
        elif is_jpeg_file(filename):
            worklist.append(filename)

    for filename in worklist:
        click.echo(f"Reading metadata for: {filename}")
        img = Image.open(filename)
        w = img.width
        h = img.height

        exif_dict = piexif.load(filename)

        curr_w = exif_dict["Exif"][piexif.ExifIFD.PixelXDimension]
        curr_h = exif_dict["Exif"][piexif.ExifIFD.PixelYDimension]

        if curr_w == w and curr_h == h:
            click.echo(f"Skipped. Metadata already correct for: {filename}")
            continue

        exif_dict["Exif"][piexif.ExifIFD.PixelXDimension] = w
        exif_dict["Exif"][piexif.ExifIFD.PixelYDimension] = h

        # Preserve original filename in the chosen output directory.
        new_filename = os.path.join(output_dir, os.path.basename(filename))
        shutil.copy2(filename, new_filename)

        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, new_filename)

        click.echo(f"Fixed metadata for: {filename}, written to {new_filename}")

if __name__ == "__main__":
    cli()
