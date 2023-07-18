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

    @pytest.mark.parametrize("lat,lon", [
        ([31.6938],
         [-85.1774])
    ])
    def test_tcwind_events(self, lat, lon):
        ret = self.dc.tcwind_events(lat, lon)
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) == len(set(df.cell_id))


    @pytest.mark.parametrize("lats,lons", [
        ([31.6938, 31.7359, 31.42, 31.532, 31.7, 31.5, 31.4, 31.1, 31.2, 31.3],
         [-85.1774, -85.1536, -85.1, -85.1, -85.1, -85.1, -85.1, -85.1, -85.1, -85.1])
    ])
    def test_tcwind_simple(self, lats, lons):
        ret = self.dc.tcwind_returnvalues(lats, lons, [100])
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) == len(lats)
 

    @pytest.mark.parametrize("min_lat,max_lat,min_lon,max_lon,n_points,return_periods", [
        (25.0,30.0,-84.0,-80.0, 10, [10,20,100,250,500]) #Florida
    ])
    def test_tcwind_returnvalues(self, min_lat, max_lat, min_lon, max_lon, n_points, return_periods):
        # Creates sample points
        return
        lats, lons = generate_random_points(min_lat, max_lat, min_lon, max_lon, n_points)

        # Use the DeepCyc client to call the API
        ret = self.dc.tcwind_returnvalues(lats, lons, return_periods)

        # Convert the results into a GeoPandas data frame
        df = gpd.GeoDataFrame.from_features(ret)

        # Tests
        assert len(df) == len(lats)
        assert len(df.iloc[0].windspeeds) == len(years)
        assert sorted(df.iloc[0].windspeeds) == df.iloc[0].windspeeds


    @pytest.mark.parametrize("lats,lons,terrain_correction", [
        ([26.26], [-83.51], ['full_terrain_gust', 'open_water', 'open_terrain', 'all_open_terrain'])
    ])
    def test_tcwind_terrain(self, lats, lons, terrain_correction):
        return
        ow = self.dc.point(lats, lons, 'Present_Day', 'OW', '1-minute')
        ow_ws = np.array(ow['features'][0]['properties']['windspeeds'])

        ow_gust = self.dc.point(lats, lons, 'Present_Day', 'OW', '3-seconds')
        ow_gust_ws = np.array(ow_gust['features'][0]['properties']['windspeeds'])

        # Check that they are all sorted
        assert (np.flip(np.sort(ow_ws)) == ow_ws).all()
        assert (np.flip(np.sort(ow_gust_ws)) == ow_gust_ws).all()

        assert (ow_gust_ws > ow_ws).all()
        assert np.round(np.mean(ow_gust_ws / ow_ws), 3) == 1.321


    @pytest.mark.parametrize("lats,lons,wind_speed_units", [
        ([26.26], [-83.51], ['kph', 'mph', 'kts', 'ms'])
    ])
    def test_tcwind_units(self, lats, lons, wind_speed_units):
        return
        ow = self.dc.point(lats, lons, 'Present_Day', 'OW', '1-minute')
        ow_ws = np.array(ow['features'][0]['properties']['windspeeds'])

        ow_gust = self.dc.point(lats, lons, 'Present_Day', 'OW', '3-seconds')
        ow_gust_ws = np.array(ow_gust['features'][0]['properties']['windspeeds'])

        # Check that they are all sorted
        assert (np.flip(np.sort(ow_ws)) == ow_ws).all()
        assert (np.flip(np.sort(ow_gust_ws)) == ow_gust_ws).all()

        assert (ow_gust_ws > ow_ws).all()
        assert np.round(np.mean(ow_gust_ws / ow_ws), 3) == 1.321

    @pytest.mark.parametrize("lats,lons,wind_speed_averaging_period", [
        ([26.26], [-83.51], ['1_minute', '3_seconds'])
    ])
    def test_tcwind_wind_speed_averaging_period(self, lats, lons, wind_speed_averaging_period):
        return
        ow = self.dc.point(lats, lons, 'Present_Day', 'OW', '1-minute')
        ow_ws = np.array(ow['features'][0]['properties']['windspeeds'])

        ow_gust = self.dc.point(lats, lons, 'Present_Day', 'OW', '3-seconds')
        ow_gust_ws = np.array(ow_gust['features'][0]['properties']['windspeeds'])

        # Check that they are all sorted
        assert (np.flip(np.sort(ow_ws)) == ow_ws).all()
        assert (np.flip(np.sort(ow_gust_ws)) == ow_gust_ws).all()

        assert (ow_gust_ws > ow_ws).all()
        assert np.round(np.mean(ow_gust_ws / ow_ws), 3) == 1.321

   
   

    def test_tcwind_events(self):
        """
        Test pointep by calculating using the point endpoint.
        """
        return

        lats = [28.999]
        lons = [-81.001]

        ret = self.dc.tcwind_events(lats, lons, terrain_correction='OT',
                    windspeed_averaging_period='1-minute')
        ot_ws = np.array(ret['features'][0]['properties']['windspeeds'])

        ret = self.dc.tcwind_events(lats, lons, terrain_correction='OT',
                    windspeed_averaging_period='3-seconds')
        ot_ws_gust = np.array(ret['features'][0]['properties']['windspeeds'])

        simulation_years = ret['header']['simulation_years']

        idx = np.argmin(abs(ot_ws - 119))

        calc_ep = idx / (simulation_years + 1)

        ret = self.dc.twwind_returnperiods(lats, lons, return_values=[119], terrain_correction='OT',
                        windspeed_averaging_period='1_minute')
        api_ep = ret['features'][0]['properties']['aeps'][0]

        assert round(calc_ep, 3) == round(api_ep, 3)

        ret = self.dc.tcwind_returnvalues(lats, lons, return_period=[100])
        assert ret['features'][0]['properties']['windspeeds'] == [166]
        assert ret['features'][0]['properties']['aeps'] == [0.01]

        ret = self.dc.tcwind_returnperiods(lats, lons, return_value=[166])
        assert ret['features'][0]['properties']['aeps'] == [0.0098]

    @pytest.mark.parametrize("lat,lon,radius_km", [
        (27.7221, -82.7386, 50)
        ,(27.7221, -82.7386, 5)
    ])
    def test_tctrack_circle(self, lat, lon, radius_km):
        return

        res = self.dc.tctrack_events(27.7221, -82.7386, geometry='circle', radius_km=50)
        assert res is not None

        res2 = self.dc.tctrack_events('circle', 27.7221, -82.7386, radius_km=5)
        assert res2 is not None

    @pytest.mark.parametrize("lats,lons", [
        ([28.556358, 28.556358], [-92.770067, -87.070986])
    ])
    def test_tctrack_line(self, lats, lons):
        return
        res = self.dc.tctrack_events(lats, lons, geometry='line')
        assert res is not None


    @pytest.mark.parametrize("lats,lons", [
        ([29, 30, 30], [-90, -90, -91])
    ])
    def test_tctrack_multiline(self, lats, lons):
        return
        res = self.dc.tctrack_events(lats, lons, geometry='line')
        assert res is not None

    @pytest.mark.parametrize("lats,lons", [
        ([29, 30, 30, 29, 29], [-91, -91, -90, -90, -91])
    ])
    def test_tctrack_polygon(self, lats, lons):
        return
        res = self.dc.tctrack_events(lats, lons, geometry='polygon')
        assert res is not None