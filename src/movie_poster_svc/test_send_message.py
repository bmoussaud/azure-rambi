import unittest

from azure.identity import ManagedIdentityCredential
from azure.storage.queue import QueueServiceClient
from main import GenAiMovieService

class TestGenAiMovieService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up any state specific to the execution of the given class."""
        cls.service = GenAiMovieService()

    @classmethod
    def tearDownClass(cls):
        """Clean up any state that was previously set up with a call to setUpClass."""
        pass

    def setUp(self):
        """Set up any state specific to the execution of the given method."""
        pass

    def tearDown(self):
        """Clean up any state that was previously set up with a call to setUp."""
        pass

    def test_generate_new_message(self):
        """Test the generate_new_message method."""
        result = self.service.generate_new_message("TestMovie")

if __name__ == '__main__':
    unittest.main()