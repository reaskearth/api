
from reaskapi.api_client import ApiClient, ClientConfig

class Metryc(ApiClient):

    def __init__(self, config_section='default'):
        """(deprecated) Initialize Metryc class"""
        super().__init__('Metryc', config_section=config_section)

    def __init__(self, config: ClientConfig = None):
        """Initialize Metryc class by ClientConfig object"""
        super().__init__('Metryc', config=config)