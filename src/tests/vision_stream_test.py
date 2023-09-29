import unittest
import cv2

from agentware.agent_logger import Logger
from agentware.senses.vision import ObjectTracker
logger = Logger()


class VisionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_objects(self):
        tracker = ObjectTracker()
        image_path = "/Users/weiduan/Projects/agentware/src/tests/suitcase_frame.png"
        # Use the cv2.imread() function to read the image
        image = cv2.imread(image_path)
        objects = tracker.get_objects(image)
        assert len(objects) == 3

    def test_track_image(self):
        tracker = ObjectTracker()
        # Track the first frame
        image1 = cv2.imread(
            "/Users/weiduan/Projects/agentware/src/tests/data/vision/frame1.png")
        tracker.track_image(image1)
        assert len(tracker.objects) == 3
        # Track the second frame
        image2 = cv2.imread(
            "/Users/weiduan/Projects/agentware/src/tests/data/vision/frame2.png")
        tracker.track_image(image2)
        # Objects should remain the same
        assert len(tracker.objects) == 3
        # Track the third frame


if __name__ == '__main__':
    unittest.main()
