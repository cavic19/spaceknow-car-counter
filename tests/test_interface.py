from dataclasses import dataclass
import unittest
from unittest.mock import patch
from spaceknow.api import KrakenApi
from spaceknow.control import TaskingManager
from spaceknow.errors import AuthorizationException
from spaceknow.interface import SpaceknowAnalysis
from PIL.Image import Image

class TestSpaceknowAnalysis(unittest.TestCase):
    @dataclass
    class DummyImage:
        index_1: int
        index_2: int
        
        def __eq__(self, o: object) -> bool:
            return o.index_1 == self.index_1 and o.index_2 == self.index_2

    def test_build_layout(self):
        sk_analysis = SpaceknowAnalysis(None,None,None,None)
        test_tiles = []
        test_images = []

        test_tiles.append((16, 24, 57))
        test_images.append(self.DummyImage(24,57))

        test_tiles.append((16, 26, 57))
        test_images.append(self.DummyImage(26, 57))

        test_tiles.append((16, 23, 56))
        test_images.append(self.DummyImage(23, 56))

        test_tiles.append((16, 23, 57))
        test_images.append(self.DummyImage(23, 57))

        test_tiles.append((16, 25, 57))
        test_images.append(self.DummyImage(25, 57))

        test_tiles.append((16, 25, 56))
        test_images.append(self.DummyImage( 25, 56))

        test_tiles.append((16, 26, 56))
        test_images.append(self.DummyImage(26, 56))

        test_tiles.append((16, 24, 56))
        test_images.append(self.DummyImage(24, 56))



        expected = [
            [self.DummyImage(23, 56),self.DummyImage( 24, 56),self.DummyImage(25, 56),self.DummyImage(26, 56)],
            [self.DummyImage(23, 57),self.DummyImage(24, 57),self.DummyImage(25, 57),self.DummyImage( 26, 57)]
        ]

        actual = list(sk_analysis._SpaceknowAnalysis__build_layout(test_tiles, test_images))

        self.assertListEqual(expected, actual)


        



        