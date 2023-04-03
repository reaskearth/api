
import sys
import requests
import random
import json
import time

from auth import get_access_token

def deepcyc_point(access_token, lats, lons, epoch='Present_Day', tag=None):

    if type(lats) != type([]):
        lats = [lats]
        lons = [lons]

    url = 'https://api.reask.earth/v1/deepcyc/point'
    params = {
        'access_token': access_token,
        'peril': 'TC_Wind',
        'lats': lats,
        'lons': lons,
    }
    if tag is not None:
        params['tag'] = tag
    if epoch is not None:
        params['epoch'] = epoch

    start_time = time.time()
    res = requests.get(url, params=params)

    print(res.url)

    if res.status_code != 200:
        print(res.text)
        return None

    print('point took {}ms'.format(round((time.time() - start_time) * 1000)))

    return res.json()

def rand_coord(start, stop):
    return random.randrange(round(start*1000), round(stop*1000)) / 1000

def main():

    access_token = get_access_token()

    # Random points in Florida
    min_lat = 25.9921875
    max_lat = 26.984375
    min_lon = -79.5
    max_lon = -79.005859375

    lats = []
    lons = []
    #for i in range(10):
    for i in range(1):
        lats.append(rand_coord(min_lat, max_lat))
        lons.append(rand_coord(min_lon, max_lon))

    ret = deepcyc_point(access_token, lats, lons, tag='Florida')
    with open('DeepCyc_Present_Day_Florida_API_Sample.json', 'w') as f:
        print(json.dumps(ret, indent=4), file=f)


if __name__ == '__main__':
    sys.exit(main())
