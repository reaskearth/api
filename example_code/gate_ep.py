
import sys
import requests
import random
import json
import time

from auth import get_access_token

def gate_ep(access_token, lats, lons, gate, epoch=None, tag=None):

    if type(lats) != type([]):
        lats = [lats]
        lons = [lons]

    url = 'https://api.reask.earth/v1/deepcyc/gateep'
    #url = 'http://api.reask.earth:5001/v1/deepcyc/gateep'
    params = {
        'access_token': access_token,
        'peril': 'TC_Wind',
        'lats': lats,
        'lons': lons,
        'gate': gate,
        'years': [20, 50, 100]
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

    lats = [30, 29, 30]
    lons = [-91, -90, -89] 

    ret = gate_ep(access_token, lats, lons, 'line', tag='New_Orleans')
    with open('New_Orleans_GateEP_DeepCyc_Present_Day_API_Sample.json', 'w') as f:
        print(json.dumps(ret, indent=4), file=f)


if __name__ == '__main__':
    sys.exit(main())
