import logging

# Create a consoler handler to output log messages to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Define the log message format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s')
console_handler.setFormatter(formatter)

# Set logging level to DEBUG and add the console handler
logging.getLogger(__name__).setLevel(logging.DEBUG)
logging.getLogger(__name__).addHandler(console_handler)