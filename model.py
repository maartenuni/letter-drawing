from __future__ import annotations

import os.path as p
import json
from typing import TypedDict
import image
import gi
import random
import space
from distractors import Distractor
import serializer

gi.require_version("Pango", "1.0")
from gi.repository import Pango


class Model:
    path: str
    name: str
    config_name = "draw.json"
    font: str
    font_description: Pango.FontDescription | None
    distractors: list[Distractor]
    distractor_font: str
    distractor_font_description: Pango.FontDescription | None
    show_path: bool
    close_path: bool
    exclusion_path: list[space.Point2D]

    rec_surf: image.RecImage

    def __init__(
        self,
        path="",
        name="",
        word="",
        font="",
        word_x=0.0,
        word_y=0.0,
        img_x=0.0,
        img_y=0.0,
        distractors: list[Distractor] = [],
        distractor_font: str = "",
        show_path: bool = False,
        close_path: bool = False,
        exclusion_path: list[space.Point2D] = [],
    ):
        self.rec_surf = image.RecImage(self)

        self.path = path
        self.name = name
        self.word = word
        self.word_x = word_x
        self.word_y = word_y

        if img_x:
            self.img_x = img_x
        else:
            self.img_x = self.rec_surf.width / 2

        if img_y:
            self.img_y = img_y
        else:
            self.img_y = self.rec_surf.height / 2

        self.font = font
        self.font_description = None
        self.distractors = distractors
        self.distractor_font = distractor_font
        self.distractor_font_description = None
        self.show_path = show_path
        self.close_path = show_path
        self.exclusion_path = exclusion_path

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def word(self) -> str:
        return self.rec_surf.word

    @word.setter
    def word(self, value: str):
        self.rec_surf.word = value

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value: str):
        if value:
            if not p.exists(value):
                raise ValueError(f"None existent path: {value}")
            else:
                self._path = value
                self.name = p.basename(value)
                self.rec_surf.fn = self.path
        else:
            self._path = ""

    @property
    def word_x(self) -> float:
        """Return the translation of the word along the x axis
        Positive direction makes the word move right, negative move it left.
        """
        return self.rec_surf.pars.word_tr_x

    @word_x.setter
    def word_x(self, value: float) -> float:
        """Return the translation of the word along the x axis
        Positive direction makes the word move right, negative move it left.
        """
        self.rec_surf.pars.word_tr_x = value

    @property
    def word_y(self) -> float:
        """Return the translation of the word along the y axis
        Positive direction makes the word move down, negative move it up.
        """
        return self.rec_surf.pars.word_tr_y

    @word_y.setter
    def word_y(self, value: float) -> float:
        """Return the translation of the word along the y axis
        Positive direction makes the word move down, negative move it up.
        """
        self.rec_surf.pars.word_tr_y = value

    @property
    def img_x(self) -> float:
        return self.rec_surf.pars.surf_tr_x

    @img_x.setter
    def img_x(self, value: float):
        self.rec_surf.pars.surf_tr_x = value

    @property
    def img_y(self) -> float:
        return self.rec_surf.pars.surf_tr_y

    @img_y.setter
    def img_y(self, value: float):
        self.rec_surf.pars.surf_tr_y = value

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "word": self.word,
            "word_x": self.word_x,
            "word_y": self.word_y,
            "img_x": self.img_x,
            "img_y": self.img_y,
            "font": self.font,
            "distractor_font": self.distractor_font,
            "show_path": self.show_path,
            "close_path": self.close_path,
            # put long lists in the end
            "exclusion_path": self.exclusion_path,
            "distractors": self.distractors,
        }

    @staticmethod
    def from_dict(d: dict) -> Model:
        return Model(**dict)

    @staticmethod
    def from_file(fn="") -> Model:
        """Load the config file for this program

        The config file should be in the same current working directory.
        if not fn, the default will be tried.
        """
        if not fn:
            fn = Model.config_name
        with open(fn, "r") as content:
            d = json.loads(content.read(), object_hook=serializer.deserializer)
            model = Model(**d)
            return model

    def add_distractor(self, string: str):
        width, height = self.rec_surf.pars.size
        point = space.Point2D(width * random.random(), height * random.random())
        while self.rec_surf.in_exclusion_path(point):
            print(f"{point} in exclusion_path")
            point.x, point.y = width * random.random(), height * random.random()
        distractor = Distractor(string, point)
        self.distractors.append(distractor)

    def get_font_desc(self) -> Pango.FontDescription | None:
        """Get the font description when specified"""
        return self.font_description

    def set_font_desc(self, font_desc: Pango.FontDescription) -> None:
        """set the font description when specified"""
        self.font_description = font_desc
        self.rec_surf.font_desc = font_desc

    def get_distractor_font_desc(self) -> Pango.FontDescription | None:
        """Get the distractor font description when specified"""
        return self.distractor_font_description

    def set_distractor_font_desc(self, font_desc: Pango.FontDescription) -> None:
        self.distractor_font_description = font_desc

    def save(self):
        with open(self.config_name, "wb") as configfile:
            configfile.write(
                json.dumps(
                    self.as_dict(),
                    indent=4,
                    default=serializer.serializer,
                ).encode("utf8")
            )
