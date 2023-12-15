
import logging
import sys
import time
import requests
from dataclasses import dataclass 
from reaskapi.auth import get_access_token

URL_MAX_BYTES = 2**15


DEFAULT_BASE_URL = 'https://api.reask.earth/v2'
DEFAULT_CONFIG_SECTION = 'default'

@dataclass
class ClientConfig:
    """Config class to customize ApiClient
    """
    config_section: str = DEFAULT_CONFIG_SECTION
    base_url: str = DEFAULT_BASE_URL


class ApiClient:
    logger = logging.getLogger(__name__)

    def __init__(self, product, config_section='default'):
        """
        (deprecated) Initialize client getting access token
        """
        self.access_token = get_access_token(config_section)
        self.product = product
        self.base_url = 'https://api.reask.earth/v2'

        self.headers = {'Content-Type':'application/json',
             'Authorization': f'Bearer {self.access_token}'}

    def __init__(self, product, config: ClientConfig=None):
        """
        Initialize client by ClientConfig
        """
        if config is None:
            config = ClientConfig() # use default values
        self.access_token = get_access_token(config.config_section)
        self.product = product
        self.base_url = config.base_url

        self.headers = {'Content-Type':'application/json',
             'Authorization': f'Bearer {self.access_token}'}


    def tcwind_events(self, lat, lon, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, f'{self.product.lower()}/tcwind/events')
    
    def tcwind_footprint(self, min_lat, max_lat, min_lon, max_lon, **kwargs):

        params = kwargs.copy()
        params['min_lat'] = min_lat
        params['max_lat'] = max_lat
        params['min_lon'] = min_lon
        params['max_lon'] = max_lon
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, f'{self.product.lower()}/tcwind/footprint')

    def tctrack_events(self, lat, lon, geometry, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        params['geometry'] = geometry
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, f'{self.product.lower()}/tctrack/events')


    def tctrack_wind_speed_events(self, lat, lon, geometry, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        params['geometry'] = geometry
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, f'{self.product.lower()}/tctrack/wind_speed/events')


    def tctrack_central_pressure_events(self, lat, lon, geometry, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        params['geometry'] = geometry
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, f'{self.product.lower()}/tctrack/central_pressure/events')


    def _call_api(self, params, endpoint):
        """
        Base method to send authenticated calls to the API HTTP endpoints
        """

        url = f'{self.base_url}/{endpoint}'

        start_time = time.time()

        # using with block to ensure connection resources are properly released
        with requests.Session() as session:

            # ensure that the request url is not too long
            req = requests.Request('GET', url, params=params,
                                     headers=self.headers).prepare()
            url_bytes = len(req.url)
            if url_bytes > URL_MAX_BYTES:
                print('Error: request url is too long. {} > {} bytes'.format(url_bytes, URL_MAX_BYTES), file=sys.stderr)
                return None

            # call the API endpoint
            res = session.send(req)

            # throw an exception in case of an error
            if res.status_code != 200:
                if res.headers['Content-Type'] == 'application/json':
                    err_msg = res.json()['detail']
                else:
                    err_msg = res.content

                self.logger.debug(err_msg)
                raise Exception(f"API returned HTTP {res.status_code} with {err_msg}")

        self.logger.info(f"querying {endpoint} took {round((time.time() - start_time) * 1000)}ms")
        
        if res.headers['Content-Type'] == 'application/json':
            self.logger.debug(res.json())
            return res.json()
        else:
            return res.content
