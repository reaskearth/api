
from reaskapi.api_client import ApiClient, ClientConfig

class Metryc(ApiClient):

    def __init__(self, config_section='default'):
        """(deprecated) Initialize Metryc class"""
        super().__init__('Metryc', config_section=config_section)

    def __init__(self, config: ClientConfig = None):
        """Initialize Metryc class by ClientConfig object"""
        super().__init__('Metryc', config=config)


    def __tcwind_footprint(self, subproduct, min_lat, max_lat, min_lon, max_lon, **kwargs):

        params = kwargs.copy()
        params['min_lat'] = min_lat
        params['max_lat'] = max_lat
        params['min_lon'] = min_lon
        params['max_lon'] = max_lon

        self.logger.debug(f'Parameters: {params}')
        return self._call_api(params, f'metryc/{subproduct}/tcwind/footprint')


    def tcwind_footprint(self, min_lat, max_lat, min_lon, max_lon, **kwargs):

        return self.__tcwind_footprint('historical', min_lat, max_lat, min_lon, max_lon, **kwargs)

    def live_tcwind_footprint(self, min_lat, max_lat, min_lon, max_lon, **kwargs):

        return self.__tcwind_footprint('live', min_lat, max_lat, min_lon, max_lon, **kwargs)

    def historical_tcwind_footprint(self, min_lat, max_lat, min_lon, max_lon, **kwargs):

        return self.__tcwind_footprint('historical', min_lat, max_lat, min_lon, max_lon, **kwargs)

    def live_tcwind_list(self, **kwargs):

        self.logger.debug(f'Parameters: {kwargs}')
        return self._call_api(kwargs, 'metryc/live/tcwind/list')

    def historical_tcwind_list(self, **kwargs):

        self.logger.debug(f'Parameters: {kwargs}')
        return self._call_api(kwargs, 'metryc/historical/tcwind/list')
