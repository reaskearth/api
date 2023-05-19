
import sys
import json
import numpy as np
import geopandas as gpd
import random
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

def generate_random_points():

    min_lat = 25.0
    max_lat = 30.0
    min_lon = -84.0
    max_lon = -80.0

    lats = []
    lons = []
    for i in range(1000):
        lat = random.randrange(round(min_lat*1e6), round(max_lat*1e6)) / 1e6
        lon = random.randrange(round(min_lon*1e6), round(max_lon*1e6)) / 1e6
        lats.append(lat)
        lons.append(lon)

    return lats, lons


def test_florida_point():

    dc = DeepCyc()

    lats, lons = generate_random_points()
    ret = dc.point(lats, lons)

    df = gpd.GeoDataFrame.from_features(ret).set_index('cell_id')
    assert len(df) == len(lats)


def test_florida_pointep():

    dc = DeepCyc()

    lats, lons = generate_random_points()
    years = [10, 20, 100, 250, 500]

    ret = dc.pointep(lats, lons, years=years)

    df = gpd.GeoDataFrame.from_features(ret).set_index('cell_id')
    assert len(df) == len(lats)
    assert len(df.iloc[0].windspeeds) == len(years)
    assert sorted(df.iloc[0].windspeeds) == df.iloc[0].windspeeds


if __name__ == '__main__':
    test_florida_pointep()
    test_florida_point()

