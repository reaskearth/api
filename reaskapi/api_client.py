
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

    deprecated_args = {
        'name': 'storm_name',
        'year': 'storm_year',
        'season': 'storm_year',
        'storm_season': 'storm_year'
    }

    def __init__(self, product, config_section='default', product_version=None):
        """
        (deprecated) Initialize client getting access token
        """
        self.access_token = get_access_token(config_section)
        self.product = product
        self.base_url = 'https://api.reask.earth/v2'

        self.headers = {'Content-Type':'application/json',
             'Authorization': f'Bearer {self.access_token}'}

        if product_version:
            self.headers['product-version'] = product_version

    def __init__(self, product, config: ClientConfig=None, product_version=None):
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

        if product_version:
            self.headers['product-version'] = product_version



    def tcwind_events(self, lat, lon, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, f'{self.product.lower()}/tcwind/events')

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

    def _call_api(self, param_args, endpoint, method='GET', post_data={}):
        """
        Base method to send authenticated calls to the API HTTP endpoints
        """

        # Normalise/fix deprecated parameters
        params = param_args.copy()
        for k in param_args.keys():
            if k in self.deprecated_args.keys():
                params[k] = self.deprecated_args[k]

        url = f'{self.base_url}/{endpoint}'

        start_time = time.time()

        # using with block to ensure connection resources are properly released
        with requests.Session() as session:

            if (method == 'GET'):
                req = requests.Request('GET', url, params=params,
                                       headers=self.headers).prepare()
            else:
                assert method == 'POST'
                req = requests.Request('POST', url, params=params,
                                       headers=self.headers, json=post_data).prepare()

            # ensure that the request url is not too long
            url_bytes = len(req.url)
            if url_bytes > URL_MAX_BYTES:
                print('Error: request url is too long. {} > {} bytes'.format(url_bytes, URL_MAX_BYTES), file=sys.stderr)
                return None

            # call the API endpoint
            res = session.send(req)

            # throw an exception in case of an error
            if res.status_code != 200:
                if 'Content-Type' in res.headers and res.headers['Content-Type'] == 'application/json':
                    err_msg = res.json()['detail']
                else:
                    err_msg = res.content

                self.logger.debug(err_msg)
                raise Exception(f"API returned HTTP {res.status_code} with {err_msg}")

        self.logger.info(f"querying {endpoint} took {round((time.time() - start_time) * 1000)}ms")

        if 'Content-Type' in res.headers and res.headers['Content-Type'] == 'application/json':
            self.logger.debug(res.json())
            return res.json()
        else:
            return res.content
