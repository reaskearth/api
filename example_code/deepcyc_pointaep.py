
import sys
import requests
import random
import json
import time

from auth import get_access_token


def deepcyc_pointaep(access_token, lats, lons, aeps=None, years=None,
                     windspeeds=None, epoch=None, tag=None):

    if type(lats) != type([]):
        lats = [lats]
        lons = [lons]

    url = 'https://api.reask.earth/v1/deepcyc/pointaep'
    params = {
        'access_token': access_token,
        'peril': 'TC_Wind',
        'lats': lats,
        'lons': lons,
    }
    if aeps is not None:
        params['aeps'] = aeps
    elif years is not None:
        params['years'] = years
    elif windspeeds is not None:
        params['windspeeds'] = windspeeds
    else:
        assert False, 'Provide one of aeps, years, windspeeds'

    if tag is not None:
        params['tag'] = tag
    if epoch is not None:
        params['epoch'] = epoch

    start_time = time.time()
    res = requests.get(url, params=params)

    if res.status_code != 200:
        print(res.text)
        return None

    print('pointaep took {}ms'.format(round((time.time() - start_time) * 1000)))

    return res.json()

def rand_coord(start, stop):
    return random.randrange(round(start*1000), round(stop*1000)) / 1000

def main():

    access_token = get_access_token()
    min_lat = 25.
    max_lat = 27.5
    min_lon = -82.5
    max_lon = -80.0

    lats = []
    lons = []
    for i in range(10):
        lats.append(rand_coord(min_lat, max_lat))
        lons.append(rand_coord(min_lon, max_lon))

    aeps = [0.1, 0.01, 0.004]
    r1 = deepcyc_pointaep(access_token, lats, lons, aeps=aeps)
    f1 = sorted(r1['features'], key=lambda f: f['properties']['cell_id'])

    years = [10, 100, 250]
    r2 = deepcyc_pointaep(access_token, lats, lons, years=years)
    f2 = sorted(r1['features'], key=lambda f: f['properties']['cell_id'])

    assert f1[0]['properties']['windspeeds'] == \
            f2[0]['properties']['windspeeds']

    ws = f1[0]['properties']['windspeeds']
    r3 = deepcyc_pointaep(access_token, lats, lons, windspeeds=ws)
    f3 = sorted(r1['features'], key=lambda f: f['properties']['cell_id'])

    assert f3[0]['properties']['aeps'] == aeps

    with open('DeepCyc_PointAEP_API_Sample.json', 'w') as f:
        print(json.dumps(r3, indent=4), file=f)


if __name__ == '__main__':
    sys.exit(main())
