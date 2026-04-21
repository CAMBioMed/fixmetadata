# Fix Metadata
Fixes the metadata on photos to allow them to be displayed and used properly on CoralNet.



## Prerequisites
Python and UV.

Python is most likely already installed. See [this page](https://docs.astral.sh/uv/getting-started/installation/) for UV installation instructions.


## Running
To run the script and see help information:

```shell
uv run fixmetadata.py fix --help
```


## Usage
Specify `fix` followed by the directories to fix. Then specify the output directory with the `--output-dir` option. For example:

```shell
uv run fixmetadata.py fix ~/Documents/MyPhotos --output-dir ~/Documents/MyPhotosFixed 
```


## Technical details
This script overwrites the `PixelXDimension` and `PixelYDimension` EXIF fields to match the actual width and height of the image.