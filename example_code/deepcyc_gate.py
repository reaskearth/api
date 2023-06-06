
import sys
import requests
import random
import json
import time

from auth import get_access_token

def deepcyc_gate(access_token, lats, lons, gate, radius_km=None, epoch=None, tag=None):

    if type(lats) != type([]):
        lats = [lats]
        lons = [lons]

    url = 'https://api.reask.earth/v1/deepcyc/gate'
    params = {
        'access_token': access_token,
        'peril': 'TC_Wind',
        'lats': lats,
        'lons': lons,
        'gate': gate,
        'return_period': [10, 25, 50, 100, 250]
    }

    if gate == 'circle':
        params['radius_km'] = radius_km
    if tag is not None:
        params['tag'] = tag
    if epoch is not None:
        params['epoch'] = epoch

    start_time = time.time()
    res = requests.get(url, params=params)

    if res.status_code != 200:
        print(res.text)
        return None

    print('gate {} took {}ms'.format(gate, round((time.time() - start_time) * 1000)))

    return res.json()


def main():

    access_token = get_access_token()

    lats = [27.7]
    lons = [-82.7]

    ret = deepcyc_gate(access_token, lats, lons, 'circle', radius_km=50, tag='Florida')
    if ret is not None:
        with open('Florida_Gate_DeepCyc_Present_Day_API_Sample.json', 'w') as f:
            print(json.dumps(ret, indent=4), file=f)


if __name__ == '__main__':
    sys.exit(main())
