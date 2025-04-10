#!/usr/bin/env python3
from space import Point2D, Vector2D
import unittest as unit
import math as m
import random


class TestPoint2D(unit.TestCase):
    """Tests various properties of points in 2d space"""

    def test_init(self):
        p1 = Point2D()
        self.assertEqual(p1.x, 0.0)
        self.assertEqual(p1.y, 0.0)
        p2 = Point2D(1, 3)
        self.assertEqual(p2.x, 1.0)
        self.assertEqual(p2.y, 3.0)

    def test_point_subtraction(self):
        p1 = Point2D(2.0, 2.0)
        v1 = Vector2D(2.0, 2.0)
        res = p1 - v1
        self.assertTrue(
            isinstance(res, Point2D),
            "Subtracting a vector from a point should yield a new Point2D",
        )
        self.assertEqual(
            res,
            Point2D(),
            f"{p1} - {v1} should bring us back to the {Point2D()}",
        )

        p2 = Point2D(4.0, 4.0)
        res = p2 - p1
        self.assertTrue(
            res, "{p2} - {p1}, should yield a Point, but type is: {type(res)}"
        )
        self.assertEqual(res, v1, "{p2}")

    def test_point_addition(self):
        p1 = Point2D(2.0, 2.0)
        v1 = Vector2D(2.0, 2.0)
        res = p1 + v1
        self.assertTrue(
            isinstance(res, Point2D),
            "Subtracting a vector from a point should yield a new Point2D",
        )
        self.assertEqual(
            res,
            Point2D(4, 4),
            f"{p1} + {v1} should bring us to {Point2D(4,4)}",
        )
        self.assertRaises(TypeError, lambda: p1 + Point2D())


class TestVector2D(unit.TestCase):
    """Tests various properties of vectors in 2d space"""

    def test_init(self):
        p1 = Vector2D()
        self.assertEqual(p1.x, 0.0)
        self.assertEqual(p1.y, 0.0)
        p2 = Vector2D(1, 3)
        self.assertEqual(p2.x, 1.0)
        self.assertEqual(p2.y, 3.0)

    def test_vector_subtraction(self):
        v1 = Point2D(2.0, 2.0)
        res = v1 - v1
        self.assertTrue(
            isinstance(res, Vector2D),
            "Subtracting a vector from a point should yield a new Vector2D",
        )
        self.assertEqual(
            res,
            Vector2D(),
            f"{v1} - {v1} should bring us back to the {Vector2D()}",
        )

    def test_vector_addition(self):
        v1 = Vector2D(2.0, 2.0)
        v2 = Vector2D(2.0, 2.0)
        v3 = Vector2D(4, 4)
        res = v1 + v1
        self.assertTrue(
            isinstance(res, Vector2D),
            "Adding a vector from a point should yield a new Vector2D",
        )
        self.assertEqual(
            res,
            v3,
            f"{v1} + {v2} should bring us to {v3}",
        )
        self.assertRaises(TypeError, lambda: v1 + Point2D())

    def test_vector_scalar_mul(self):
        scalar = 3
        v1 = Vector2D(1, 1)
        self.assertEqual(v1 * scalar, Vector2D(3, 3))

    def test_vector_magnitude(self):
        v0 = Vector2D()
        v1 = Vector2D(1, 1)
        self.assertEqual(v0.magnitude, 0)
        self.assertEqual(v1.magnitude, m.sqrt(2))

    def test_unit(self):
        for i in range(10):
            v1 = Vector2D(random.random() * 10, random.random() * 10)
            u = v1.unit
            vorg = u * v1.magnitude
            self.assertAlmostEqual(u.magnitude, 1.0)
            self.assertAlmostEqual(vorg.x, v1.x)
            self.assertAlmostEqual(vorg.y, v1.y)


if __name__ == "__main__":
    unit.main()
