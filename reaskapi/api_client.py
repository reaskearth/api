
import time
import requests
from reaskapi.auth import get_access_token

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
        res = requests.get(self.base_url + endpoint, params=params)

        if res.status_code != 200:
            print(res.text)
            return None

        print('querying {} points took {}ms'.format(len(params['lats']), round((time.time() - start_time) * 1000)))

        return res.json()
