#!/bin/usr/env python3

from PIL import Image
from PIL.ImageFile import ImageFile
import cairo as c
import typing

PBGen = typing.Generator[bytes, Image.Image, None]


def _genCairoBytesFromPilRGB(img: Image):
    """Generate byte sequence in cairo image ordering

    PIL's RGB is a format of 3 bytes([R, G, B]) per pixel,
    cairo's RGB is a 4 bytes quantity bytes ([unused, R, G, B])

    So for every 3 bytes of PIL's RGB image, four bytes of cairo's pixels are
    yielded from the output.
    """
    imgbytes = img.tobytes()
    unusedbyte = bytes([0])  # put a 0 on the unused byte value
    for i in range(0, len(imgbytes), 3):
        yield imgbytes[i + 2]
        yield imgbytes[i + 1]
        yield imgbytes[i + 0]
        yield unusedbyte[0]


def _genCairoBytesFromPilRGBA(img: Image):
    """Generate byte sequence in cairo image ordering

    PIL's RGBA is a format of 4 bytes([R, G, B, A]) per pixel,
    cairo's ARGB32 is a 4 bytes quantity bytes ([A, R, G, B])
    """
    imgbytes = img.tobytes()
    for i in range(0, len(imgbytes), 4):
        yield imgbytes[i + 2]
        yield imgbytes[i + 1]
        yield imgbytes[i + 0]
        yield imgbytes[i + 3]


def _convertToSurf(img: Image, Format: c.Format, gen_func: PBGen) -> c.ImageSurface:
    """Converts an PIL.Image to a surface."""
    imgbytes = bytearray(gen_func(img))
    surf = c.ImageSurface.create_for_data(
        imgbytes,
        Format,
        img.width,
        img.height,
        Format.stride_for_width(img.width),
    )
    return surf


def pilImageToCairoSurf(img: ImageFile, f: c.Format) -> c.ImageSurface:
    """Turn a pillow Image into a Cairo.Surface"""
    mode = img.mode

    # Currently we only handle these images directly
    if mode not in ["RGB", "RGBA"]:
        img = img.convert("RGB")

    if mode == "RGB":
        return _convertToSurf(img, f, _genCairoBytesFromPilRGB)
    else:
        return _convertToSurf(img, f, _genCairoBytesFromPilRGBA)


if __name__ == "__main__":
    from PIL import ImageDraw
    import time

    img = Image.new("RGBA", [500, 500], (255, 255, 255))

    draw = ImageDraw.Draw(img)
    bx, by = img.width / 4, img.height / 2
    size = 50.0
    hsize = 25
    height = 250 - hsize
    draw.ellipse([bx * 1 - hsize, height, bx * 1 + hsize, height + size], (255, 0, 0))
    draw.ellipse([bx * 2 - hsize, height, bx * 2 + hsize, height + size], (0, 255, 0))
    draw.ellipse([bx * 3 - hsize, height, bx * 3 + hsize, height + size], (0, 0, 255))

    img.save("pil.png", "PNG")

    t1 = time.time()
    surf = pilImageToCairoSurf(img, c.FORMAT_RGB24)
    t2 = time.time()
    print(f"It took {t2 - t1}")
    surf.write_to_png("cairo.png")
