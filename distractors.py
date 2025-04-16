#!/usr/bin/env python3

import space
import serializer


class Distractor:
    def __init__(self, string: str, pos: space.Point2D):
        self.string = string
        self.pos = pos


def json_serialize_distractor(distractor: Distractor) -> dict:
    if isinstance(distractor, Distractor):
        return {
            "__distractor__": True,
            "string": distractor.string,
            "pos_x": distractor.pos.x,
            "pos_y": distractor.pos.y,
        }
    raise TypeError(f"distractor is not of class {Distractor.__name__}")


def json_deserialize_distractor(dct):
    if "__distractor__" in dct:
        point = space.Point2D(dct["pos_x"], dct["pos_y"])
        return Distractor(dct["string"], point)
    return dct


# register (de-)serialization functions
serializer.serializer.register_serializer(Distractor, json_serialize_distractor)
serializer.deserializer.register_deserializer(Distractor, json_serialize_distractor)
