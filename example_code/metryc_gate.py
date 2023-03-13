
import sys
import requests
import random
import json
import time

from auth import get_access_token

def metryc_gate(access_token, lats, lons, gate, radius=None, tag=None):

    if type(lats) != type([]):
        lats = [lats]
        lons = [lons]

    url = 'https://api.reask.earth/v1/metryc/gate'
    params = {
        'access_token': access_token,
        'peril': 'TC_Wind',
        'lats': lats,
        'lons': lons,
        'gate': gate,
    }

    if gate == 'circle':
        assert radius is not None
        params['radius_km'] = radius
    if tag is not None:
        params['tag'] = tag

    start_time = time.time()
    res = requests.get(url, params=params)

    if res.status_code != 200:
        print(res.text)
        return None

    print('Metryc gate {} took {}ms'.format(gate, round((time.time() - start_time) * 1000)))

    return res.json()


def main():

    access_token = get_access_token()

    lats = [28, 27.5, 25, 25, 27.5, 30]
    lons = [-83, -83, -81.5, -79.5, -79.5, -80]

    ret = metryc_gate(access_token, lats, lons, 'line', tag='Florida')
    with open('Florida_Line_Gate_Metryc_API_Sample.json', 'w') as f:
        print(json.dumps(ret, indent=4), file=f)

    lats = [30]
    lons = [-90]
    ret = metryc_gate(access_token, lats, lons, 'circle', radius=50, tag='New_Orleans')
    with open('New_Orleans_Circle_Gate_Metryc_API_Sample.json', 'w') as f:
        print(json.dumps(ret, indent=4), file=f)


if __name__ == '__main__':
    sys.exit(main())
