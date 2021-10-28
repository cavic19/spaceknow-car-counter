from dataclasses import dataclass
import unittest
from unittest.mock import patch
from spaceknow.api import KrakenApi
from spaceknow.control import TaskingManager
from spaceknow.interface import SpaceknowAnalysis
from spaceknow.models import Tiles
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
        test_map_id = '123456789'
        test_tiles = Tiles(test_map_id)
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

    # def test_count_cars(self):
    #     sk_analysis = SpaceknowAnalysis(
    #         kraken_api=None,
    #         tasking_manager=TaskingManager(),
    #         scene_ids=None,
    #         extent=None)
    #     retrieved_tiles = {}
    #     features = []

    #     with patch('spaceknow.control.TaskingManager.wait_untill_completed', lambda s,x: retrieved_tiles):
    #         with patch('spaceknow.api.KrakenApi.get_detections', lambda s: features):
    #             pass



        