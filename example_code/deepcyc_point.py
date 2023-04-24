
import sys
import requests
import random
import json
import numpy as np
import time

from auth import get_access_token

def deepcyc_point(access_token, lats, lons, terrain_correction='OW',
                  windspeed_averaging_period='1-minute', epoch='Present_Day', tag=None):

    assert terrain_correction in ['OW', 'OT', 'AOT', 'FT_GUST']
    assert windspeed_averaging_period in ['3-seconds', '1-minute']

    if type(lats) != type([]):
        lats = [lats]
        lons = [lons]

    url = 'https://api.reask.earth/v1/deepcyc/point'
    params = {
        'access_token': access_token,
        'peril': 'TC_Wind',
        'lats': lats,
        'lons': lons,
        'windspeed_averaging_period': windspeed_averaging_period,
        'terrain_correction': terrain_correction
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

    print('point took {}ms'.format(round((time.time() - start_time) * 1000)))

    return res.json()

def rand_coord(start, stop):
    return random.randrange(round(start*1000), round(stop*1000)) / 1000

def main():

    access_token = get_access_token()

    # Random points in Florida
    min_lat = 25.
    max_lat = 27.5
    min_lon = -82.5
    max_lon = -80.0

    lats = []
    lons = []
    for i in range(2):
        lats.append(rand_coord(min_lat, max_lat))
        lons.append(rand_coord(min_lon, max_lon))

    ow = deepcyc_point(access_token, lats, lons, terrain_correction='OW', 
                       windspeed_averaging_period='1-minute', tag='Florida')
    ow_ws = ow['features'][0]['properties']['windspeeds']

    ot = deepcyc_point(access_token, lats, lons, terrain_correction='OT', 
                       windspeed_averaging_period='1-minute', tag='Florida')
    ot_ws = ot['features'][0]['properties']['windspeeds']


if __name__ == '__main__':
    sys.exit(main())
