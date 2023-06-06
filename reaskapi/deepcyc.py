
import time
import requests
from reaskapi.api_client import ApiClient

class DeepCyc(ApiClient):

    def __init__(self):
        super().__init__('DeepCyc')

    def point(self, lats, lons, epoch='Present_Day',
              terrain_correction='FT_GUST',
              windspeed_averaging_period='3-seconds', tag=None):

        params = {
            'lats': lats,
            'lons': lons,
            'units': 'kph',
            'terrain_correction': terrain_correction,
            'windspeed_averaging_period': windspeed_averaging_period
        }
        if tag is not None:
            params['tag'] = tag
        if epoch is not None:
            params['epoch'] = epoch

        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, 'point')


    def pointep(self, lats, lons, years=None, windspeeds=None,
                terrain_correction='FT_GUST',
                windspeed_averaging_period='3-seconds', tag=None):

        params = {
            'peril': 'TC_Wind',
            'lats': lats,
            'lons': lons,
            'terrain_correction': terrain_correction,
            'windspeed_averaging_period': windspeed_averaging_period
        }
        if years is not None:
            params['years'] = years
        if windspeeds is not None:
            params['windspeeds'] = windspeeds
        if tag is not None:
            params['tag'] = tag

        self.logger.debug(f'Parameters: {params}')

        params['access_token'] = self.access_token
        return self._call_api(params, 'pointaep')


    def gateep(self, gate, lats, lons, radius_km=50, years=None, windspeeds=None,
               epoch='Present_Day', tag=None):

        params = {
            'access_token': self.access_token,
            'peril': 'TC_Wind',
            'lats': lats,
            'lons': lons,
            'gate': gate,
        }

        if years:
            params['years'] = years
        if windspeeds:
            params['windspeeds'] = windspeeds
        if gate == 'circle':
            params['radius_km'] = radius_km
        if tag is not None:
            params['tag'] = tag
        if epoch is not None:
            params['epoch'] = epoch

        return self._call_api(params, 'deepcyc/gateaep')


    def gate(self, gate, lats, lons, radius_km=50, epoch='Present_Day', tag=None):

        params = {
            'access_token': self.access_token,
            'peril': 'TC_Wind',
            'lats': lats,
            'lons': lons,
            'gate': gate,
        }

        if gate == 'circle':
            params['radius_km'] = radius_km
        if tag is not None:
            params['tag'] = tag
        if epoch is not None:
            params['epoch'] = epoch

        return self._call_api(params, 'gate')
