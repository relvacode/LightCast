import io
import typing
import itertools

import colorgram
from PIL import Image

RGB = typing.Tuple[float, float, float]

MAX_SAMPLE_SIZE = 256


def extract_palette(f: io.BytesIO | Image.Image, colors: int, downsample: bool = True) -> list[RGB]:
    image = f if isinstance(f, Image.Image) else Image.open(f)
    if image.mode not in ('RGB', 'RGBA', 'RGBa'):
        image = image.convert('RGB')

    # Downsample image
    if downsample and (image.width > MAX_SAMPLE_SIZE or image.height > MAX_SAMPLE_SIZE):
        aspect = MAX_SAMPLE_SIZE / float(image.width)
        height = int(float(image.height) * aspect)
        image = image.resize((MAX_SAMPLE_SIZE, height), resample=Image.Resampling.NEAREST)

    extracted_colors = colorgram.extract(image, colors)

    palette = []
    for i, color in zip(range(colors), itertools.cycle(extracted_colors)):
        palette.append((color.rgb.r, color.rgb.g, color.rgb.b))

    return palette


if __name__ == "__main__":
    def main():
        import sys

        with open(sys.argv[1], 'rb') as f:
            palette = extract_palette(f, int(sys.argv[2]))
            for color in palette:
                print(color)


    main()
