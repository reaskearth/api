
import sys
import requests
import json
import geopandas as gpd

from auth import get_access_token

"""
This example shows how to load Metryc storm footprints from the OGC Features API.
"""

def metryc_collections(access_token, bbox, do_load=False):
    """
    Load Metryc TC footprint features in the given bbox.
    """

    url = 'https://api.reask.earth/v1/ogcapi/collections'
    params = {
        'access_token': access_token,
        'bbox': '{},{},{},{}'.format(bbox['min_lon'], bbox['min_lat'],
                                     bbox['max_lon'], bbox['max_lat'])
    }

    res = requests.get(url, params=params)
    assert res.status_code == 200

    # Get a list of all collections/storms
    ids = [coll['id'] for coll in res.json()['collections'] if 'metryc' in coll['id']]

    print('Available Metryc storms: ')
    print('{}'.format('\n'.join(ids)))

    if not do_load:
        return

    # Load features
    for id in ids:
        coll_url = '{}/{}/items'.format(url, id)

        ret = requests.get(coll_url, params=params).json()
        if len(ret['features']) > 0:
            print('Loading {} with {} features'.format(id, len(ret['features'])))
            df = gpd.GeoDataFrame.from_features(ret).set_index('cell_id')


def main():

    access_token = get_access_token()
    tampa_florida_bbox = {'min_lat': 27.0, 'max_lat': 28.0,
                          'min_lon': -83.0, 'max_lon': -82.0}

    metryc_collections(access_token, tampa_florida_bbox, do_load=True, do_save=False)


if __name__ == '__main__':
    sys.exit(main())
