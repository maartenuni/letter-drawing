#!/usr/bin/env python3
import cairo
import argparse as ap


def draw(file: str, width: int, height: int, scale=1.0) -> None:
    """Draws a file on an image of width * height and saves it"""

    with open(file, "rb") as source_file:
        source_surf = cairo.ImageSurface.create_from_png(source_file)

    target_surf = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)

    cr = cairo.Context(target_surf)

    # set bg to gray
    cr.set_source_rgb(0.5, 0.5, 0.5)
    cr.paint()

    # In order to scale a surface image, you'll need to scale the pattern, not
    # the path!
    pattern = cairo.SurfacePattern(source_surf)
    mat = cairo.Matrix()
    mat.scale(scale, scale)
    pattern.set_matrix(mat)

    cr.set_source(pattern)

    cr.rectangle(0, 0, width, height)

    cr.fill()

    target_surf.write_to_png("draw.png")


def main():
    """draw an image"""
    parser = ap.ArgumentParser("draw.py", "draw a picture")
    parser.add_argument("file", type=str, help="the file used as source surface")
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=500,
        help="the width of the target surface",
    )
    parser.add_argument(
        "-H",
        "--height",
        type=int,
        default=500,
        help="the height of the target surface",
    )
    parser.add_argument(
        "-s",
        "--scale",
        type=float,
        default=1.0,
        help="apply scaling to the source surface",
    )

    args = parser.parse_args()

    draw(args.file, args.width, args.height, args.scale)


if __name__ == "__main__":
    main()
