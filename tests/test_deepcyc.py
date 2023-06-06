import geopandas as gpd
import numpy as np
import pytest
import random
import sys

from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

def generate_random_points(min_lat, max_lat, min_lon, max_lon, n_points):

    # min_lat = 25.0
    # max_lat = 30.0
    # min_lon = -84.0
    # max_lon = -80.0

    lats = []
    lons = []

    for i in range(n_points):
        lat = random.randrange(round(min_lat*1e6), round(max_lat*1e6)) / 1e6
        lon = random.randrange(round(min_lon*1e6), round(max_lon*1e6)) / 1e6
        lats.append(lat)
        lons.append(lon)

    return lats, lons

class TestDeepCycApi():
    dc = DeepCyc()

    @pytest.mark.parametrize("min_lat,max_lat,min_lon,max_lon,n_points,years", [
        (25.0,30.0,-84.0,-80.0, 10, [10,20,100,250,500]) #Florida
    ])
    def test_pointaep(self, min_lat, max_lat, min_lon, max_lon, n_points, years):
        # Creates sample points
        lats, lons = generate_random_points(min_lat, max_lat, min_lon, max_lon, n_points)

        # Use the DeepCyc client to call the API
        ret = self.dc.pointep(lats, lons, years=years)

        # Convert the results into a GeoPandas data frame
        df = gpd.GeoDataFrame.from_features(ret).set_index('cell_id')

        # Tests
        assert len(df) == len(lats)
        assert len(df.iloc[0].windspeeds) == len(years)
        assert sorted(df.iloc[0].windspeeds) == df.iloc[0].windspeeds

    @pytest.mark.parametrize("lats,lons", [
        ([26.26], [-83.51])
    ])
    def test_point_ow(self, lats, lons):
        ow = self.dc.point(lats, lons, 'Present_Day', 'OW', '1-minute')
        ow_ws = np.array(ow['features'][0]['properties']['windspeeds'])

        ow_gust = self.dc.point(lats, lons, 'Present_Day', 'OW', '3-seconds')
        ow_gust_ws = np.array(ow_gust['features'][0]['properties']['windspeeds'])

        # Check that they are all sorted
        assert (np.flip(np.sort(ow_ws)) == ow_ws).all()
        assert (np.flip(np.sort(ow_gust_ws)) == ow_gust_ws).all()

        assert (ow_gust_ws > ow_ws).all()
        assert np.round(np.mean(ow_gust_ws / ow_ws), 3) == 1.321
    
    @pytest.mark.parametrize("lats,lons", [
        ([26.26], [-83.51])
    ])
    def test_point_aot(self, lats, lons):
        aot = self.dc.point(lats, lons, 'Present_Day', terrain_correction='AOT', windspeed_averaging_period='1-minute')
        aot_ws = np.array(aot['features'][0]['properties']['windspeeds'])

        aot_gust = self.dc.point(lats, lons, terrain_correction='AOT', windspeed_averaging_period='3-seconds')
        aot_gust_ws = np.array(aot_gust['features'][0]['properties']['windspeeds'])

        assert (aot_gust_ws > aot_ws).all()
        assert np.round(np.mean(aot_gust_ws / aot_ws), 3) == 1.423        

    @pytest.mark.parametrize("lats,lons", [
        ([31.6938, 31.7359, 31.42, 31.532, 31.7, 31.5, 31.4, 31.1, 31.2, 31.3],
         [-85.1774, -85.1536, -85.1, -85.1, -85.1, -85.1, -85.1, -85.1, -85.1, -85.1])
    ])
    def test_point_simple(self, lats, lons):
        ret = self.dc.point(lats, lons)
        df = gpd.GeoDataFrame.from_features(ret).set_index('cell_id')

        assert len(df) == len(lats)
    

    def test_pointaep(self):
        """
        Test pointep by calculating using the point endpoint.
        """

        lats = [28.999]
        lons = [-81.001]

        ret = self.dc.point(lats, lons, terrain_correction='OT',
                    windspeed_averaging_period='1-minute')
        ot_ws = np.array(ret['features'][0]['properties']['windspeeds'])

        ret = self.dc.point(lats, lons, terrain_correction='OT',
                    windspeed_averaging_period='3-seconds')
        ot_ws_gust = np.array(ret['features'][0]['properties']['windspeeds'])

        simulation_years = ret['header']['simulation_years']

        idx = np.argmin(abs(ot_ws - 119))

        calc_ep = idx / (simulation_years + 1)

        ret = self.dc.pointaep(lats, lons, windspeeds=[119], terrain_correction='OT',
                        windspeed_averaging_period='1-minute')
        api_ep = ret['features'][0]['properties']['aeps'][0]

        assert round(calc_ep, 3) == round(api_ep, 3)

        ret = self.dc.pointaep(lats, lons, years=[100])
        assert ret['features'][0]['properties']['windspeeds'] == [166]
        assert ret['features'][0]['properties']['aeps'] == [0.01]

        ret = self.dc.pointaep(lats, lons, windspeeds=[166])
        assert ret['features'][0]['properties']['aeps'] == [0.0098]