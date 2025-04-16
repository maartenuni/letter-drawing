#!/usr/bin/env python3

from collections.abc import Callable


class _CustomSerializer:
    """Serializers objects to json, the types must be register a function before
    this class know how to serialize them
    """

    def __init__(self):
        self.class_serializers = {}

    def register_serializer(self, tp: type, function: Callable):
        self.class_serializers[tp] = function

    def __call__(self, obj: object) -> dict:
        tp = type(obj)
        if tp not in self.class_serializers:
            raise TypeError(f"We don't know how to serialize an instance of {tp}")
        return self.class_serializers[tp](obj)


class _CustomDeSerializer:
    """DeSerializes json to python object, the types must register a function before
    this class knows how to deserialize them into python objects
    """

    def __init__(self):
        self.deserializer_keys = {}

    def register_deserializer(self, json_str: str, function: Callable):
        self.deserializer_keys[json_str] = function

    def __call__(self, dct) -> object:
        for key in self.deserializer_keys.keys():
            if key in dct:
                return self.deserializer_keys[key](dct)
        return dct


serializer = _CustomSerializer()
deserializer = _CustomDeSerializer()
