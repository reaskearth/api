
import sys
import requests
import random
import json
import time

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

    with open('DeepCyc_PointEP_API_Sample.json', 'w') as f:
        print(json.dumps(r2, indent=4), file=f)


if __name__ == '__main__':
    sys.exit(main())
