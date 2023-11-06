
import time
from reaskapi.api_client import ApiClient

class DeepCyc(ApiClient):

    def __init__(self, config_section='default'):
        super().__init__('DeepCyc', config_section=config_section)

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

    def tctrack_wind_speed_returnperiods(self, lat, lon, return_value, geometry, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        params['return_value'] = return_value
        params['geometry'] = geometry
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'deepcyc/tctrack/wind_speed/returnperiods')

    def tctrack_central_pressure_returnperiods(self, lat, lon, return_value, geometry, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        params['return_value'] = return_value
        params['geometry'] = geometry
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'deepcyc/tctrack/central_pressure/returnperiods')

    def tctrack_returnvalues(self, lat, lon, return_period, geometry, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        params['return_period'] = return_period
        params['geometry'] = geometry
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'deepcyc/tctrack/returnvalues')

    def tctrack_wind_speed_returnvalues(self, lat, lon, return_period, geometry, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        params['return_period'] = return_period
        params['geometry'] = geometry
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'deepcyc/tctrack/wind_speed/returnvalues')

    def tctrack_central_pressure_returnvalues(self, lat, lon, return_period, geometry, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        params['return_period'] = return_period
        params['geometry'] = geometry
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'deepcyc/tctrack/central_pressure/returnvalues')