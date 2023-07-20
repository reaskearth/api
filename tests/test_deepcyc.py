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
        lats, lons = generate_random_points(min_lat, max_lat, min_lon, max_lon, n_points)

        # Use the DeepCyc client to call the API
        ret = self.dc.tcwind_returnvalues(lats, lons, return_periods)

        # Convert the results into a GeoPandas data frame
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) == len(lats) * len(return_periods)

        df_one = df[df.cell_id == df.iloc[0].cell_id]
        assert sorted(df_one.wind_speed) == list(df_one.wind_speed)
        assert list(df_one.return_period) == return_periods

    @pytest.mark.parametrize("terrain_correction", [
        'full_terrain_gust', 'open_water', 'open_terrain', 'all_open_terrain'
    ])
    def test_tcwind_terrain(self, terrain_correction):
        lats, lons = generate_random_points(25, 30, -85, -80, 1)

        ret = self.dc.tcwind_returnvalues(lats, lons, 100, terrain_correction=terrain_correction,
                                              wind_speed_averaging_period='3_seconds')
        df_gust = gpd.GeoDataFrame.from_features(ret)

        try:
            ret = self.dc.tcwind_returnvalues(lats, lons, 100, terrain_correction=terrain_correction,
                                                wind_speed_averaging_period='1_minute')
        except Exception as e:
            assert terrain_correction == 'full_terrain_gust'
            assert 'Unsupported terrain correction type' in str(e)

        if terrain_correction != 'full_terrain_gust':
            df_sus = gpd.GeoDataFrame.from_features(ret)
            assert df_gust.iloc[0].wind_speed > df_sus.iloc[0].wind_speed

    @pytest.mark.parametrize("wind_speed_units", ['kph', 'mph', 'kts', 'ms'])
    def test_tcwind_units(self, wind_speed_units):
        lats, lons = generate_random_points(25, 30, -85, -80, 1)

        ret_kph = self.dc.tcwind_returnvalues(lats, lons, 100)
        ws_kph = ret_kph['features'][0]['properties']['wind_speed']

        ret = self.dc.tcwind_returnvalues(lats, lons, 100, wind_speed_units=wind_speed_units)
        ws_other = ret['features'][0]['properties']['wind_speed']

        if wind_speed_units == 'kph':
            multiplier = 1
        elif wind_speed_units == 'mph':
            multiplier = 1.609344
        elif wind_speed_units == 'kts':
            multiplier = 1.8520000118528
        elif wind_speed_units == 'ms':
            multiplier = 3.6

        assert ws_kph == round(ws_other*multiplier)

    def test_tcwind_events(self):
        """
        Test return period and value by calculating using the events endpoint.
        """
        lats = [28.999]
        lons = [-81.001]

        ret = self.dc.tcwind_events(lats, lons)
        df = gpd.GeoDataFrame.from_features(ret)
        ws = np.array(df.wind_speed)
        simulation_years = ret['header']['simulation_years']

        calculated_rp = simulation_years / np.argmin(abs(ws - 119))

        ret = self.dc.tcwind_returnperiods(lats, lons, return_value=119)
        api_rp = ret['features'][0]['properties']['return_period']

        assert round(calculated_rp) == round(api_rp)

    @pytest.mark.parametrize("lat,lon", [
        (27.7221, -82.7386)
    ])
    def test_tctrack_circle(self, lat, lon):

        ret = self.dc.tctrack_events(lat, lon, 'circle', radius_km=50)
        df1 = gpd.GeoDataFrame.from_features(ret)

        ret = self.dc.tctrack_events(lat, lon, 'circle', radius_km=5)
        df2 = gpd.GeoDataFrame.from_features(ret)

        assert set(df2.event_id).issubset(set(df1.event_id))

    @pytest.mark.parametrize("lats,lons", [
        ([28.556358, 28.556358], [-88.770067, -87.070986])
    ])
    def test_tctrack_line(self, lats, lons):
        ret = self.dc.tctrack_events(lats, lons, 'line')
        df = gpd.GeoDataFrame.from_features(ret)
        assert len(df) > 12000

    @pytest.mark.parametrize("lats,lons", [
        ([29, 30, 30], [-90, -90, -91])
    ])
    def test_tctrack_multiline(self, lats, lons):
        ret = self.dc.tctrack_events(lats, lons, 'line')
        df = gpd.GeoDataFrame.from_features(ret)
        assert len(df) > 12000

    @pytest.mark.parametrize("lats,lons", [
        ([29, 30, 30, 29, 29], [-91, -91, -90, -90, -91])
    ])
    def test_tctrack_polygon(self, lats, lons):
        ret = self.dc.tctrack_events(lats, lons, 'polygon')
        df = gpd.GeoDataFrame.from_features(ret)
        assert len(df) > 14000