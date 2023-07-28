import geopandas as gpd
import numpy as np
import pytest
import random
import sys
import json
import shapely
from pyproj import Transformer

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

class TestDeepcyc():
    dc = DeepCyc()

    @pytest.mark.parametrize("lat,lon", [
        # CONUS, Australia
        ([31.6938, -20.35685],
         [-85.1774, 148.95112])
    ])
    def test_tcwind_events(self, lat, lon):
        ret = self.dc.tcwind_events(lat, lon)
        df = gpd.GeoDataFrame.from_features(ret)

        assert ret['header']['message'] is None
        assert len(lat) == len(set(df.cell_id))

    @pytest.mark.parametrize("lats,lons", [
        ([31.6938, 31.7359, 31.42, 31.532, 31.7, 31.5, 31.4, 31.1, 31.2, 31.3],
         [-85.1774, -85.1536, -85.1, -85.1, -85.1, -85.1, -85.1, -85.1, -85.1, -85.1])
    ])
    def test_tcwind_simple(self, lats, lons):
        ret = self.dc.tcwind_returnvalues(lats, lons, [100])
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) == len(lats)

    @pytest.mark.parametrize("scenario,time_horizon", [
        ('SSP1-2.6', 2035),
        ('SSP2-4.5', 2035),
        ('SSP5-8.5', 2035),
        ('SSP1-2.6', 2050),
        ('SSP2-4.5', 2050),
        ('SSP5-8.5', 2050),
    ])
    def test_tcwind_future_climate(self, scenario, time_horizon):

        lats, lons = generate_random_points(27.5, 28.5, -85, -80, 1)
        lats.extend([25.15, 25.15])
        lons.extend([-80.735, -80.725])
        return_periods = [100]

        ret1 = self.dc.tcwind_returnvalues(lats, lons, return_periods,
                                             scenario='current_climate', time_horizon='now')
        assert ret1['header']['simulation_years'] == 41000
        df_now = gpd.GeoDataFrame.from_features(ret1)

        ret2 = self.dc.tcwind_returnvalues(lats, lons, return_periods,
                                            scenario=scenario, time_horizon=time_horizon)
        assert ret2['header']['simulation_years'] == 25000
        df_future = gpd.GeoDataFrame.from_features(ret2)

        assert (df_now.wind_speed < df_future.wind_speed).all()


    @pytest.mark.parametrize("num_points", [
        (1000),
    ])
    def test_tcwind_many_points(self, num_points):

        lats, lons = generate_random_points(27.5, 33, -100, -80, num_points)
        return_periods = [10, 25, 50, 100, 250, 500, 750]

        ret1 = self.dc.tcwind_returnvalues(lats, lons, return_periods,
                                            scenario='current_climate', time_horizon='now')
        df1 = gpd.GeoDataFrame.from_features(ret1)
        df1.sort_values(by=['cell_id', 'return_period'], inplace=True)
        assert len(df1) == len(return_periods) * num_points

        ret2 = self.dc.tcwind_returnvalues(lats, lons, return_periods,
                                            scenario='current_climate', time_horizon='now')
        df2 = gpd.GeoDataFrame.from_features(ret2)
        df2.sort_values(by=['cell_id', 'return_period'], inplace=True)
        assert len(df1) == len(return_periods) * num_points

        assert list(df1.wind_speed) == list(df2.wind_speed)


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

    def test_tcwind_calc_rp(self):
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

        radius_km = 10
        ret1 = self.dc.tctrack_events(lat, lon, 'circle', radius_km=radius_km)
        geom1 = shapely.from_geojson(json.dumps(ret1['header']['query_geometry']))

        aeqd_crs = f"+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0"
        transformer = Transformer.from_crs("EPSG:4326", aeqd_crs, always_xy=True)

        xx, yy = transformer.transform(*geom1.exterior.coords.xy)
        circle = shapely.Polygon(list(zip(xx, yy)))
        expected_area = np.pi*((radius_km*1000)**2)
        assert (1 - (circle.area / expected_area)) < 0.002

        radius_km = 5
        ret2 = self.dc.tctrack_events(lat, lon, 'circle', radius_km=radius_km)
        geom2 = shapely.from_geojson(json.dumps(ret2['header']['query_geometry']))

        xx, yy = transformer.transform(*geom2.exterior.coords.xy)
        circle = shapely.Polygon(list(zip(xx, yy)))
        expected_area = np.pi*((radius_km*1000)**2)
        assert (1 - (circle.area / expected_area)) < 0.002

        df1 = gpd.GeoDataFrame.from_features(ret1)
        df2 = gpd.GeoDataFrame.from_features(ret2)

        assert len(set(df2.event_id)) == len(df2.event_id)
        assert len(set(df1.event_id)) == len(df1.event_id)
        assert len(df2) < len(df1)
        assert set(df2.event_id).issubset(set(df1.event_id))

    @pytest.mark.parametrize("lats,lons", [
        ([28.5, 28.5], [-88.5, -88.25])
    ])
    def test_tctrack_line(self, lats, lons):
        ret = self.dc.tctrack_events(lats, lons, 'line')
        df = gpd.GeoDataFrame.from_features(ret)
        assert len(df) > 1500

    @pytest.mark.parametrize("lats,lons", [
        ([29, 29.25, 29.25], [-90, -90, -90.25])
    ])
    def test_tctrack_multiline(self, lats, lons):
        ret = self.dc.tctrack_events(lats, lons, 'line')
        df = gpd.GeoDataFrame.from_features(ret)
        assert len(df) > 3000

    @pytest.mark.parametrize("lats,lons", [
        ([29, 30, 30, 29, 29], [-91, -91, -90, -90, -91])
    ])
    def test_tctrack_polygon(self, lats, lons):
        return_periods = [100, 200]
        ret = self.dc.tctrack_returnvalues(lats, lons, return_periods, 'polygon')
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df.wind_speed) == len(return_periods)

    @pytest.mark.parametrize("lats,lons", [
        ([29, 30, 30], [-90, -90, -91])
    ])
    def test_tctrack_returnperiod_line(self, lats, lons):
        ret = self.dc.tctrack_returnperiods(lats, lons, 119, 'line')
        df = gpd.GeoDataFrame.from_features(ret)
        df.iloc[0].wind_speed == 119
        df.iloc[0].return_period < 10

    @pytest.mark.parametrize("lats,lons", [
        ([29, 30, 30, 29, 29], [-91, -91, -90, -90, -91])
    ])
    def test_tctrack_returnperiod_polygon(self, lats, lons):
        ret = self.dc.tctrack_returnperiods(lats, lons, 119, 'polygon')
        df = gpd.GeoDataFrame.from_features(ret)
        df.iloc[0].wind_speed == 119
        df.iloc[0].return_period < 10

    @pytest.mark.skip(reason='FIXME: update github secrets to contain limited permission test user')
    @pytest.mark.parametrize("lats,lons", [
        ([-20.5, -20.3, -20.3536], [148.5, 149.5, 148.9573]),
    ])
    def test_tcwind_perms(self, lats, lons):

        tmp_dc = DeepCyc(config_section='hamilton_island')
        # Use the DeepCyc client to call the API
        return_periods = [10, 25, 50, 100, 250, 500]
        ret1 = tmp_dc.tcwind_returnvalues(lats, lons, return_periods)
        df1 = gpd.GeoDataFrame.from_features(ret1)

        assert len(set(df1.cell_id)) == 1
        assert ret1['header']['message'] == 'Error: one or more requested locations either unsupported or unauthorized.'

        lats = [-20.3536]
        lons = [148.9573]
        ret2 = tmp_dc.tcwind_returnvalues(lats, lons, return_periods)
        df2 = gpd.GeoDataFrame.from_features(ret2)

        assert ret1['features'] == ret2['features']

    @pytest.mark.skip(reason='FIXME: update github secrets to contain limited permission test user')
    @pytest.mark.parametrize("lats,lons", [
        ([28.556358, 28.556358], [-88.770067, -87.070986])
    ])
    def test_tctrack_noperms(self, lats, lons):

        tmp_dc = DeepCyc(config_section='hamilton_island')
        try:
            ret = tmp_dc.tctrack_events(lats, lons, 'line')
            assert False, 'Should not get here'
        except Exception as e:
            assert '403' in str(e)