
import logging
import sys
import time
import requests
from reaskapi.auth import get_access_token

URL_MAX_BYTES = 2**15

class ApiClient:
    logger = logging.getLogger(__name__)

    def __init__(self, product, config_section='default'):
        """
        Initialize client getting access token
        """
        self.access_token = get_access_token(config_section)
        self.product = product
        self.base_url = 'https://api.reask.earth/dev'

        self.headers = {'Content-Type':'application/json',
             'Authorization': f'Bearer {self.access_token}'}

    def tcwind_riskscores(self, lat, lon, **kwargs):

        params = kwargs.copy()
        params['lat'] = lat
        params['lon'] = lon
        self.logger.debug(f'Parameters: {params}')

        return self._call_api(params, f'{self.product.lower()}/tcwind/riskscores')

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
                err_msg = res.json()['detail']
                self.logger.debug(err_msg)
                raise Exception(f"API returned HTTP {res.status_code} with {err_msg}")

        self.logger.info(f"querying {endpoint} took {round((time.time() - start_time) * 1000)}ms")
        self.logger.debug(res.json())

        return res.json()
