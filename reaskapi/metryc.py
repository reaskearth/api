
from reaskapi.api_client import ApiClient, ClientConfig

class Metryc(ApiClient):

    def __init__(self, config_section='default'):
        """(deprecated) Initialize Metryc class"""
        super().__init__('Metryc', config_section=config_section)

    def __init__(self, config: ClientConfig = None):
        """Initialize Metryc class by ClientConfig object"""
        super().__init__('Metryc', config=config)


    def tcwind_footprint(self, min_lat, max_lat, min_lon, max_lon, **kwargs):

        params = kwargs.copy()
        params['min_lat'] = min_lat
        params['max_lat'] = max_lat
        params['min_lon'] = min_lon
        params['max_lon'] = max_lon
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'metryc/tcwind/footprint')

    def live_tcwind_list(self, **kwargs):

        params = kwargs.copy()
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'metryc/live/tcwind/list')

    def historical_tcwind_list(self, **kwargs):

        params = kwargs.copy()
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'metryc/historical/tcwind/list')
