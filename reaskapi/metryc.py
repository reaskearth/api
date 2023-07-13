
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

        return self._call_api(params, 'metryc/point')

    def gate(self, lats, lons, gate, radius=None, tag=None):
        """
        Endpoint to query Metryc for a Gate
        """
        # ensure lats and lons are lists
        if type(lats) != type([]):
            lats = [lats]
            lons = [lons]

        params = {
            'lats': lats,
            'lons': lons,
            'gate': gate,
        }

        if gate == 'circle':
            assert radius is not None
            params['radius_km'] = radius
        if tag is not None:
            params['tag'] = tag

        return self._call_api(params, 'metryc/gate')

    def collections(self, bbox):
        """
        Query Metryc Collections given a rectangular bounding box
        """

        params = {
            'bbox': f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}"
        }

        return self._call_api(params, 'ogcapi/collections')