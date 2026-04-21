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

    fixed_count = 0
    skipped_count = 0
    error_count = 0

    for filename in worklist:
        name = os.path.basename(filename)
        try:
            img = Image.open(filename)
            w = img.width
            h = img.height

            try:
                exif_dict = piexif.load(filename)
            except Exception:
                click.echo(f"{name}: ERROR: No readable EXIF data")
                error_count += 1
                continue

            # Preserve original filename in the chosen output directory.
            new_filename = os.path.join(output_dir, os.path.basename(filename))
            shutil.copy2(filename, new_filename)

            exif_section = exif_dict.get("Exif") or {}
            if (
                piexif.ExifIFD.PixelXDimension not in exif_section
                or piexif.ExifIFD.PixelYDimension not in exif_section
            ):
                click.echo(f"{name}: Skipped, as it has no metadata to correct")
                skipped_count += 1
                continue

            curr_w = exif_section[piexif.ExifIFD.PixelXDimension]
            curr_h = exif_section[piexif.ExifIFD.PixelYDimension]

            if curr_w == w and curr_h == h:
                click.echo(f"{name}: Skipped, as the metadata was already correct")
                skipped_count += 1
                continue

            exif_dict["Exif"][piexif.ExifIFD.PixelXDimension] = w
            exif_dict["Exif"][piexif.ExifIFD.PixelYDimension] = h

            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, new_filename)

            fixed_count += 1
            click.echo(f"{name}: Fixed metadata")
        except Exception as e:
            click.echo(f"{name}: ERROR: {e}")
            error_count += 1

    click.echo(
        "Summary: "
        f"fixed={fixed_count}, skipped={skipped_count}, errors={error_count}, total={len(worklist)}"
    )

if __name__ == "__main__":
    cli()
