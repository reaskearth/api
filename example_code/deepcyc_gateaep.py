
import sys
import requests
import random
import json
import time

from auth import get_access_token

def deepcyc_gateaep(access_token, lats, lons, gate, epoch=None, tag=None):

    if type(lats) != type([]):
        lats = [lats]
        lons = [lons]

    url = 'https://api.reask.earth/v1/deepcyc/gateaep'
    params = {
        'access_token': access_token,
        'peril': 'TC_Wind',
        'lats': lats,
        'lons': lons,
        'gate': gate,
        'aeps': [0.05, 0.02, 0.01]
    }

    if gate == 'circle':
        params['radius_km'] = 50
    if tag is not None:
        params['tag'] = tag
    if epoch is not None:
        params['epoch'] = epoch

    start_time = time.time()
    res = requests.get(url, params=params)

    if res.status_code != 200:
        print(res.text)
        return None

    print('gateep {} took {}ms'.format(gate, round((time.time() - start_time) * 1000)))

    return res.json()


def main():

    access_token = get_access_token()

    lats = [28, 27.5, 25, 25, 27.5, 30]
    lons = [-83, -83, -81.5, -79.5, -79.5, -80]

    ret = deepcyc_gateaep(access_token, lats, lons, 'line', tag='Florida')
    with open('Florida_GateAEP_DeepCyc_Present_Day_API_Sample.json', 'w') as f:
        print(json.dumps(ret, indent=4), file=f)


if __name__ == '__main__':
    sys.exit(main())
