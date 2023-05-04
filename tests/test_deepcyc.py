
import sys
import json
import numpy as np
import geopandas as gpd
import random
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

def test_florida_point():

    min_lat = 25.0
    max_lat = 30.0
    min_lon = -84.0
    max_lon = -80.0

    lats = []
    lons = []
    for i in range(1000):
        lat = random.randrange(round(min_lat*1000), round(max_lat*1000)) / 1000
        lon = random.randrange(round(min_lon*1000), round(max_lon*1000)) / 1000
        lats.append(lat)
        lons.append(lon)

    dc = DeepCyc()

    ret = dc.point(lats, lons)

    df = gpd.GeoDataFrame.from_features(ret).set_index('cell_id')
    assert len(df) == len(lats)


if __name__ == '__main__':
    test_florida_point()

