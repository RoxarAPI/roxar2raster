"Roxar 2 raster unit tests."

import unittest
import sys
import json
import numpy
import roxar2raster


class TestMargin(unittest.TestCase):
    def test_None(self):
        surface = None
        with self.assertRaises(numpy.AxisError):
            roxar2raster.get_margin(surface)

if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(not result.result.wasSuccessful())

