"Roxar 2 raster unit tests."

import unittest
import sys
import numpy
import numpy.ma
import roxar2raster


class TestPad(unittest.TestCase):
    def test_pad_frame(self):
        surface = [[1.0] * 5] * 5  # 5 x 5 matrix
        mask = numpy.array([[False] * 5] * 5)
        mask[0][0] = True

        surface = numpy.ma.masked_array(surface, mask)
        surface = roxar2raster.pad_frame(surface)

        self.assertIs(surface[0][0], numpy.ma.masked)
        self.assertIs(surface[1][1], numpy.ma.masked)
        self.assertIs(surface[2][2], numpy.ma.masked)
        self.assertIsNot(surface[3][3], numpy.ma.masked)

        self.assertEqual(surface.data[0][0], 1.0)
        self.assertEqual(surface.data[1][1], 1.0)
        self.assertEqual(surface.data[2][2], 1.0)
        self.assertEqual(surface.data[3][3], 1.0)

    def test_pad_border(self):
        surface = numpy.array([[1.0] * 5] * 5)  # 5 x 5 matrix
        mask = numpy.array([[True] * 5] * 5)

        surface[2][2] = 2.0
        mask[2][2] = False

        surface = numpy.ma.masked_array(surface, mask)

        surface = roxar2raster.pad_border(surface)

        self.assertIs(surface[0][0], numpy.ma.masked)
        self.assertIs(surface[1][1], numpy.ma.masked)
        self.assertIsNot(surface[2][2], numpy.ma.masked)
        self.assertIsNot(surface[2][1], numpy.ma.masked)

        self.assertEqual(surface.data[0][0], 1.0)
        self.assertEqual(surface.data[1][1], 1.0)
        self.assertEqual(surface.data[2][2], 2.0)
        self.assertEqual(surface.data[2][1], 2.0)

    def test_pad(self):
        surface = numpy.array([[1.0] * 5] * 5)  # 5 x 5 matrix
        mask = numpy.array([[True] * 5] * 5)

        surface[2][2] = 2.0
        mask[2][2] = False

        surface = numpy.ma.masked_array(surface, mask)

        padded_surface = roxar2raster.pad(surface)

        self.assertIs(padded_surface[0][0], numpy.ma.masked)
        self.assertIs(padded_surface[3][3], numpy.ma.masked)
        self.assertIsNot(padded_surface[4][4], numpy.ma.masked)

        self.assertEqual(padded_surface.data[0][0], 1.0)
        self.assertEqual(padded_surface.data[2][2], 1.0)
        self.assertEqual(padded_surface.data[3][3], 2.0)
        self.assertEqual(padded_surface.data[4][4], 2.0)

        self.assertEqual(surface.shape[0] + 4, padded_surface.shape[0])
        self.assertEqual(surface.shape[1] + 4, padded_surface.shape[1])


class TestMargin(unittest.TestCase):
    def test_none(self):
        surface = None
        with self.assertRaises(numpy.AxisError):
            roxar2raster.get_margin(surface)

    def test_empty(self):
        surface = []
        with self.assertRaises(numpy.AxisError):
            roxar2raster.get_margin(surface)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(not result.result.wasSuccessful())
