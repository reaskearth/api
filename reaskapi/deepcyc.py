
import time
from reaskapi.api_client import ApiClient

class DeepCyc(ApiClient):

    def __init__(self, config_section='default'):
        super().__init__('DeepCyc', config_section=config_section)


    def tcwind_riskscores(self, lat, lon, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'deepcyc/tcwind/riskscores')

    def tcwind_returnperiods(self, lat, lon, return_value, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        params['return_value'] = return_value
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'deepcyc/tcwind/returnperiods')

    def tcwind_returnvalues(self, lat, lon, return_period, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        params['return_period'] = return_period
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'deepcyc/tcwind/returnvalues')


    def tctrack_returnperiods(self, lat, lon, return_value, geometry, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        params['return_value'] = return_value
        params['geometry'] = geometry
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'deepcyc/tctrack/returnperiods')


    def tctrack_returnvalues(self, lat, lon, return_period, geometry, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        params['return_period'] = return_period
        params['geometry'] = geometry
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'deepcyc/tctrack/returnvalues')
