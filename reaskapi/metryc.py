
from reaskapi.api_client import ApiClient

class Metryc(ApiClient):

    def __init__(self, config_section='default'):
        super().__init__('Metryc', config_section=config_section)