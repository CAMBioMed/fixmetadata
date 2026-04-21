import os
import shutil
from pathlib import Path
from typing import Any, TypeAlias

import click
import piexif
from PIL import Image

WorkItem: TypeAlias = tuple[str, str]
ExifDict: TypeAlias = dict[str, Any]

@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option(
    "--output-dir",
    "-o",
    required=True,
    type=click.Path(file_okay=False, dir_okay=True, path_type=str),
    help="Directory where fixed files are written.",
)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    default=False,
    show_default=True,
    help="Recursively include JPEG files from subdirectories.",
)
@click.argument("filenames", nargs=-1, required=True)
def fix(output_dir: str, recursive: bool, filenames: tuple[str, ...]) -> None:
    """Fix metadata for one or more files or directories."""
    os.makedirs(output_dir, exist_ok=True)

    def is_jpeg_file(path: str) -> bool:
        return os.path.isfile(path) and Path(path).suffix.lower() in {".jpg", ".jpeg"}

    worklist: list[WorkItem] = []
    for filename in filenames:
        if os.path.isdir(filename):
            if recursive:
                for root, _, files in os.walk(filename):
                    worklist.extend(
                        (filename, os.path.relpath(os.path.join(root, f), filename))
                        for f in files
                        if is_jpeg_file(os.path.join(root, f))
                    )
            else:
                worklist.extend(
                    (filename, f)
                    for f in os.listdir(filename)
                    if is_jpeg_file(os.path.join(filename, f))
                )
        elif is_jpeg_file(filename):
            worklist.append((os.path.dirname(filename) or ".", os.path.basename(filename)))

    fixed_count: int = 0
    skipped_count: int = 0
    error_count: int = 0

    for root_dir, relative_path in worklist:
        filename: str = os.path.join(root_dir, relative_path)
        name: str = relative_path
        try:
            img: Image.Image = Image.open(filename)
            w: int = img.width
            h: int = img.height

            try:
                exif_dict: ExifDict = piexif.load(filename)
            except Exception:
                click.echo(f"{name}: ERROR: No readable EXIF data")
                error_count += 1
                continue

            new_filename: str = os.path.join(output_dir, relative_path)
            os.makedirs(os.path.dirname(new_filename), exist_ok=True)
            shutil.copy2(filename, new_filename)

            exif_section_obj: Any = exif_dict.get("Exif") or {}
            if not isinstance(exif_section_obj, dict):
                click.echo(f"{name}: Skipped, no metadata to correct")
                skipped_count += 1
                continue

            exif_section: dict[int, Any] = exif_section_obj
            if (
                piexif.ExifIFD.PixelXDimension not in exif_section
                or piexif.ExifIFD.PixelYDimension not in exif_section
            ):
                click.echo(f"{name}: Skipped, no metadata to correct")
                skipped_count += 1
                continue

            curr_w: int = int(exif_section[piexif.ExifIFD.PixelXDimension])
            curr_h: int = int(exif_section[piexif.ExifIFD.PixelYDimension])

            if curr_w == w and curr_h == h:
                click.echo(f"{name}: Skipped, metadata was already correct")
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
