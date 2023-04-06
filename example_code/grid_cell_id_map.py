
import sys
import json
import geopandas as gpd

from auth import get_access_token
from deepcyc_point import deepcyc_point

"""
This example shows how to map between the global grid cell ids returned by the API and
lat, lon locations.
"""

RKG_RES = 2**-7 + 2**-9
RKG_NUM_COLS = int(360 / RKG_RES)
RKG_NUM_ROWS = int(180 / RKG_RES)

def latlon_from_id(id):
    """
    Returns lower left corner of cell with given id
    """

    col_idx = id % RKG_NUM_COLS
    row_idx = id // RKG_NUM_COLS

    left_lon = (col_idx*RKG_RES + 180) % 360 - 180
    lower_lat = row_idx*RKG_RES - 90 

    return (lower_lat, left_lon)


def id_from_latlon(lat, lon):
    """
    Returns cell id given lat, lon.
    """

    col_idx = int((lon % 360) / RKG_RES)
    row_idx = int((lat + 90) / RKG_RES)

    id = row_idx*RKG_NUM_COLS + col_idx

    return id


def main():

    access_token = get_access_token()

    lats = [25.1, 25.2]
    lons = [-80.24, -80.1]

    # Get some data from API and load into GeoPandas
    ret = deepcyc_point(access_token, lats, lons)
    df = gpd.GeoDataFrame.from_features(ret).set_index('cell_id')
    cell_geometry = df.iloc[0].geometry

    # Get center of grid cell
    mid_lat = cell_geometry.centroid.y
    mid_lon = cell_geometry.centroid.x

    # Calculate and check cell id
    cell_id = id_from_latlon(mid_lat, mid_lon)
    assert cell_id == df.index[0]

    # Calculate and check lower left corner of grid cell
    lower_lat, left_lon = latlon_from_id(cell_id)

    (minx, miny, maxx, maxy) = cell_geometry.bounds
    assert minx == left_lon
    assert miny == lower_lat


if __name__ == '__main__':
    sys.exit(main())
