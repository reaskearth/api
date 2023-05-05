
import sys
import time
import requests
from reaskapi.auth import get_access_token

URL_MAX_BYTES = 2**15

class ApiClient:

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
        session = requests.Session()

        req = requests.Request('GET', self.base_url + endpoint, params=params).prepare()
        url_bytes = len(req.url)
        if url_bytes > URL_MAX_BYTES:
            print('Error: request url is too long. {} > {} bytes'.format(url_bytes, URL_MAX_BYTES), file=sys.stderr)
            return None

        res = session.send(req)

        if res.status_code != 200:
            print(res.text)
            return None

        print('querying {} points took {}ms'.format(len(params['lats']), round((time.time() - start_time) * 1000)))

        return res.json()
