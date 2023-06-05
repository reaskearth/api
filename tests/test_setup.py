import logging
import unittest

class TestSetup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger(__name__)
        # Create a consoler handler to output log messages to the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Define the log message format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s')
        console_handler.setFormatter(formatter)

        # Set logging level to DEBUG and add the console handler
        cls.logger.setLevel(logging.INFO)
        cls.logger.addHandler(console_handler)