
import sys
import json
import logging
import numpy as np
import geopandas as gpd
import random
import unittest

from pathlib import Path

from test_setup import TestSetup

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

def generate_random_points():

    min_lat = 25.0
    max_lat = 30.0
    min_lon = -84.0
    max_lon = -80.0

    lats = []
    lons = []
    #for i in range(1000):
    for i in range(10):
        lat = random.randrange(round(min_lat*1e6), round(max_lat*1e6)) / 1e6
        lon = random.randrange(round(min_lon*1e6), round(max_lon*1e6)) / 1e6
        lats.append(lat)
        lons.append(lon)

    return lats, lons

class TestDeepCycApi(TestSetup):
    dc = DeepCyc()

    def test_florida_pointaep(self):
        self.logger.info('Testing DeepCyc point api')
        # Tests DeepCyc Point AEP
        #dc = DeepCyc()

        # Creates sample points
        lats, lons = generate_random_points()

        # List of years
        years = [10, 20, 100, 250, 500]

        # Use the DeepCyc client to call the API
        ret = self.dc.pointep(lats, lons, years=years)

        # Convert the results into a GeoPandas data frame
        df = gpd.GeoDataFrame.from_features(ret).set_index('cell_id')

        # Tests
        self.assertEqual(len(df), len(lats))
        self.assertEqual(len(df.iloc[0].windspeeds), len(years))
        self.assertEqual(sorted(df.iloc[0].windspeeds), df.iloc[0].windspeeds)

    # def test_florida_point(self):
    #     #dc = DeepCyc()
    #     self.logger.info('Testing DeepCyc point API call')
    #     lats, lons = generate_random_points()
    #     ret = self.dc.point(lats, lons)

    #     df = gpd.GeoDataFrame.from_features(ret).set_index('cell_id')
    #     assert len(df) == len(lats)

    # TODO: Implement test for Gate AEP API call
    # def test_gateaep(self):


if __name__ == '__main__':
    #test_florida_pointep()
    #test_florida_point()
    unittest.main()

