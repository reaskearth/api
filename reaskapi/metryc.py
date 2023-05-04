
import time
import requests
from reaskapi.auth import get_access_token
from reaskapi.api_client import ApiClient

class Metryc(ApiClient):

    def __init__(self):
        super().__init__('Metryc')

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

        return self._call_api(params, 'point')
