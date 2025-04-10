from PIL import Image

import imgutils
import cairo
from dataclasses import dataclass

import gi

gi.require_version("PangoCairo", "1.0")
gi.require_version("Pango", "1.0")
from gi.repository import PangoCairo as pc
from gi.repository import Pango

import random

ONE_INCH = 25.4  # mm

A4_WIDTH, A4_HEIGHT = 210, 297
DPI = 300


def image_ppi(size_mm: float, dpi: int):
    # calculate the number of pixels per inch
    return round(size_mm / ONE_INCH * dpi)


@dataclass
class ImageParameters:
    """Class for storing parameter for an image that are toggleable
    from the GUI"""

    size: tuple[int, int] = image_ppi(A4_WIDTH, DPI), image_ppi(A4_HEIGHT, DPI)

    surf_tr_x: float = 0
    surf_tr_y: float = 0
    surf_width: float = 0
    surf_height: float = 0
    surf_scaled_width: float = 0
    surf_scaled_height: float = 0
    surf_scale_estimate = 1.0
    _surf_scale: float = 1.0
    _surf_scale_factor: float = 0.5

    word_tr_y: float = 0.0
    word_tr_x: float = 0.0

    @property
    def width(self):
        return self.size[0]

    @property
    def height(self):
        return self.size[1]

    @property
    def ratio(self) -> float:
        return self.height / self.width

    @property
    def surf_scale_factor(self) -> float:
        return self._surf_scale_factor

    @surf_scale_factor.setter
    def surf_scale_factor(self, value):
        self._surf_scale_factor = value
        self.surf_scale = self.surf_scale_estimate * self.surf_scale_factor

    @property
    def surf_scale(self) -> float:
        return self._surf_scale

    @surf_scale.setter
    def surf_scale(self, value: float):
        self._surf_scale = value
        self.surf_scaled_width = self.surf_width * self.surf_scale
        self.surf_scaled_height = self.surf_height * self.surf_scale

    def estimate_image_pars(self):
        im_ratio = self.surf_height / self.surf_width

        if self.ratio < im_ratio:
            self.surf_scale_estimate = self.height / self.surf_height
        else:
            self.surf_scale_estimate = self.width / self.surf_width

        # Shrink the image by 10 percent
        self.surf_scale = self.surf_scale_estimate * self.surf_scale_factor

        # Calculate translation distances to center the image
        self.surf_tr_x = (self.width - self.surf_scaled_width) / 2.0
        self.surf_tr_y = (self.height - self.surf_scaled_height) / 2.0


class RecImage:
    """An image that records the operations done to it.
    you can use it's operations in order to draw on another
    image.
    """

    surf: cairo.RecordingSurface | None
    img_surf: cairo.ImageSurface | None
    fn: str
    pars: ImageParameters
    font_desc: Pango.FontDescription | None
    distractors: list[str]
    distractor_font_description: Pango.FontDescription | None

    def __init__(
        self,
        fn="",
        word="",
        font_desc: Pango.FontDescription | None = None,
        distractors: list[str] = [],
        distractor_font_description: Pango.FontDescription | None = None,
    ):
        self.surf = None
        self.img_surf = None
        self.pars = ImageParameters()
        self.font_desc = font_desc

        self.distractor_font_description = distractor_font_description
        self.distractors = distractors

        self.fn = fn
        self.word = word
        self.draw()

    @property
    def fn(self) -> str:
        return self._fn

    @fn.setter
    def fn(self, filename: str):
        self._fn = filename
        if self.fn:
            self._cacheSurf(self.fn)
        else:
            self.img_surf = None

    @property
    def width(self):
        return self.pars.size[0]

    @property
    def height(self):
        return self.pars.size[1]

    def draw(self):
        """Draw the image"""
        rect = cairo.Rectangle(0, 0, self.pars.width, self.pars.height)
        self.surf = cairo.RecordingSurface(cairo.CONTENT_COLOR, rect)
        cr = cairo.Context(self.surf)
        cr.set_source_rgb(1, 1, 1)
        cr.paint()

        if not self.img_surf:  # if we have a surface no need to update
            if self.fn:
                self._cacheSurf(cr, self.fn)
        else:
            self._drawImage(cr)

        if self.word:
            self._drawWord(cr)

        if self.distractors:
            self._draw_distractors(cr)

    def _drawImage(self, cr: cairo.Context):
        cr.save()

        pattern = cairo.SurfacePattern(self.img_surf)
        mat = cairo.Matrix()
        mat.scale(1 / self.pars.surf_scale, 1 / self.pars.surf_scale)
        mat.translate(-self.pars.surf_tr_x, -self.pars.surf_tr_y)
        pattern.set_matrix(mat)

        cr.set_source(pattern)
        cr.translate(self.pars.surf_tr_x, self.pars.surf_tr_y)
        cr.rectangle(0, 0, self.pars.surf_scaled_width, self.pars.surf_scaled_height)

        cr.fill()
        cr.restore()

    def _drawWord(self, cr):
        """Draws the word onto the surface"""

        cr.save()

        cr.set_source_rgb(0, 0, 0)

        # Update using DPI, so we get the same ~same size when drawing for
        # dpi 96 (default,pc) or dpi 300 (printing default)
        font_desc: Pango.FontDescription
        if not self.font_desc:
            font_desc = Pango.font_description_from_string("sans bold 60")
        else:
            font_desc = self.font_desc

        layout = pc.create_layout(cr)
        layout_context = layout.get_context()  # needed to change DPI
        pc.context_set_resolution(layout_context, DPI)
        layout.set_font_description(font_desc)
        layout.set_text(self.word)

        width, height = layout.get_size()
        width, height = width / Pango.SCALE, height / Pango.SCALE

        pc.update_layout(cr, layout)

        # center the layout around the origin
        cr.translate(-width / 2.0, -height / 2.0)
        # center the layout around in the middle of the image
        cr.translate(self.width / 2, self.height / 2)
        # apply user specified translations
        cr.translate(self.pars.word_tr_x, self.pars.word_tr_y)

        pc.layout_path(cr, layout)

        cr.stroke()

        cr.restore()

    def _draw_distractors(self, cr):
        """Draw the distractors"""
        cr.save()
        cr.set_source_rgb(0, 0, 0)

        # Update using DPI, so we get the ~same size when drawing for
        # dpi 96 (default,pc) or dpi 300 (printing default)
        font_desc: Pango.FontDescription
        if not self.distractor_font_description:
            font_desc = Pango.font_description_from_string("sans bold 30")
        else:
            font_desc = self.distractor_font_description

        layout = pc.create_layout(cr)
        pc.context_set_resolution(layout.get_context(), DPI)
        print(font_desc.to_string())
        layout.set_font_description(font_desc)
        width, height = layout.get_size()
        # width, height = width / Pango.SCALE, height / Pango.SCALE

        pc.update_layout(cr, layout)

        for d in self.distractors:
            cr.save()

            layout.set_text(d)

            x, y = random.randint(0, self.width), random.randint(0, self.height)

            cr.translate(x, y)

            pc.layout_path(cr, layout)

            cr.stroke()

            cr.restore()

        cr.restore()

    def _cacheSurf(self, fn: str):
        """Caches the image as a Cairo.ImageSurface"""
        with Image.open(fn) as inpic:
            if inpic.mode not in ["RGBA", "RGB"]:
                inpic = inpic.convert("RGB")

            self.img_surf = imgutils.pilImageToCairoSurf(inpic, cairo.FORMAT_RGB24)
            self.pars.surf_width = self.img_surf.get_width()
            self.pars.surf_height = self.img_surf.get_height()

            self.pars.estimate_image_pars()  # update new default values

    def save(self, fn="rec_image.png"):
        self.draw()
        self.surf.write_to_png(fn)
