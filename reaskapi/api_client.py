
import logging
import sys
import time
import requests
from reaskapi.auth import get_access_token

URL_MAX_BYTES = 2**15

class ApiClient:
    logger = logging.getLogger(__name__)

    def __init__(self, product):

        self.access_token = get_access_token()
        self.product = product
        self.base_url = 'https://api.reask.earth/v1/{}/'.format(product.lower())
        #self.base_url = 'http://api.reask.earth:5001/v1/{}/'.format(product.lower())


    def _call_api(self, params, endpoint):

        for k in ['lats', 'lons', 'years', 'windspeeds']:
            if k in params and not isinstance(params[k], list):
                params[k] = [params[k]]

        params['access_token'] = self.access_token
        params['peril'] = 'TC_Wind'

        start_time = time.time()

        # using with block to ensure connection resources are properly released
        with requests.Session() as session:

            # ensure that the request url is not too long
            req = requests.Request('GET', self.base_url + endpoint, params=params).prepare()
            url_bytes = len(req.url)
            if url_bytes > URL_MAX_BYTES:
                print('Error: request url is too long. {} > {} bytes'.format(url_bytes, URL_MAX_BYTES), file=sys.stderr)
                return None

            # call the API endpoint
            res = session.send(req)

            # throw an exception in case of an error
            if res.status_code != 200:
                self.logger.debug(res.text)
                raise Exception(f'API returned an error: {res.status_code}')

        self.logger.info('querying {} points took {}ms'.format(len(params['lats']), round((time.time() - start_time) * 1000)))
        self.logger.debug(res.json())

        return res.json()
