
import sys
import requests
import random
import json
import time

from auth import get_access_token


def deepcyc_pointep(access_token, lats, lons, epoch=None, tag=None):

    if type(lats) != type([]):
        lats = [lats]
        lons = [lons]

    url = 'https://api.reask.earth/v1/deepcyc/pointep'
    params = {
        'access_token': access_token,
        'peril': 'TC_Wind',
        'lats': lats,
        'lons': lons,
        'years': [5, 10, 25, 50, 100, 250]
    }
    if tag is not None:
        params['tag'] = tag
    if epoch is not None:
        params['epoch'] = epoch

    start_time = time.time()
    res = requests.get(url, params=params)

    if res.status_code != 200:
        print(res.text)
        return None

    print('pointep took {}ms'.format(round((time.time() - start_time) * 1000)))

    return res.json()


def main():

    access_token = get_access_token()
    min_lat = 32.5
    max_lat = 37.5
    min_lon = 130.0
    max_lon = 140.0

    lats = []
    lons = []
    for i in range(10):
        lat = random.randrange(round(min_lat*1000), round(max_lat*1000)) / 1000
        lon = random.randrange(round(min_lon*1000), round(max_lon*1000)) / 1000
        lats.append(lat)
        lons.append(lon)

    ret = deepcyc_pointep(access_token, lats, lons, tag='Japan')
    with open('Japan_DeepCyc_Present_Day_API_Sample.json', 'w') as f:
        print(json.dumps(ret, indent=4), file=f)


if __name__ == '__main__':
    sys.exit(main())
