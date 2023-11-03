
from reaskapi.api_client import ApiClient, ClientConfig

class Metryc(ApiClient):

    def __init__(self, config_section='default', config: ClientConfig = None):
        super().__init__('Metryc', config_section=config_section, config=config)