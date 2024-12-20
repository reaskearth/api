import geopandas as gpd
import numpy as np
import pytest
import random
import sys
import json
import shapely
import time
from pyproj import Transformer

from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

def generate_random_points(min_lat, min_lon, max_lat=None, max_lon=None, n_points=1):

    if max_lat is None:
        max_lat = min_lat + 0.5
    if max_lon is None:
        max_lon = min_lon + 0.5

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
    dc_v206 = DeepCyc(product_version='DeepCyc-2.0.6')
    dc_v207 = DeepCyc(product_version='DeepCyc-2.0.7')
    dc_v208 = DeepCyc(product_version='DeepCyc-2.0.8')

    @pytest.mark.parametrize("lat,lon", [
        (19.71538, -155.544),  # Hawaii
        (-17.68298, 177.2756), # Fiji
        (31.6938, -85.1774),   # CONUS
        (-20.35685, 148.9511), # Australia
        (22.25, 114.20)        # Hong Kong
    ])
    def test_tcwind_events(self, lat, lon):
        ret = self.dc.tcwind_events(lat, lon)
        assert 'DeepCyc Events' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)

        assert (df.status == 'OK').all()
        assert len(set(df.cell_id)) == 1


    @pytest.mark.parametrize("terrain_correction", [
        'full_terrain_gust',
        'open_water',
        'open_terrain'
    ])
    @pytest.mark.parametrize("lat,lon", [
        (-17.68298, 177.2756),  # Fiji
        (31.6938, -85.1774),    # CONUS
        (-20.35685, 148.95112), # Australia
        (14.0, 121),            # Philippines
        (22.25, 114.20),        # Hong Kong
        (-35.5, 174),           # New Zealand
        (31.28418, -79.995117)  # Charleston Coast
    ])
    def test_tcwind_locations(self, lat, lon, terrain_correction):

        if terrain_correction == 'full_terrain_gust':
            ws_avg = '3_seconds'
        else:
            ws_avg = '1_minute'
        ret = self.dc.tcwind_returnvalues(lat, lon, [10, 100],
                terrain_correction=terrain_correction,
                wind_speed_averaging_period=ws_avg)
        assert ret['header']['terrain_correction'] == terrain_correction
        assert ret['header']['wind_speed_averaging_period'] == ws_avg

        df = gpd.GeoDataFrame.from_features(ret)
        assert set(df.status) == {'OK'}

        assert len(set(df.cell_id)) == 1


    @pytest.mark.parametrize("lat,lon", [
        (-17.68298, 177.2756),  # Fiji
        (31.6938, -85.1774),    # CONUS
        (-20.35685, 148.95112), # Australia
        (14.0, 121),            # Philippines
        (22.25, 114.20),        # Hong Kong
        (-35.5, 174)            # New Zealand
    ])
    def test_tcwind_performance(self, lat, lon):

        lats, lons = generate_random_points(lat, lon, n_points=100)
        start_time = time.time()
        ret = self.dc.tcwind_returnvalues(lats, lons, [100])
        print('Querying 100 points took {}s'.format(time.time() - start_time))
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) == 100


    @pytest.mark.parametrize("lats,lons", [
        ([-17.6525, 31.6938, 31.7359, 31.42, 31.532, 31.7, 31.5, 31.4, 31.1, 31.2, 31.3],
         [177.2634, -85.1774, -85.1536, -85.1, -85.1, -85.1, -85.1, -85.1, -85.1, -85.1, -85.1])
    ])
    def test_tcwind_simple(self, lats, lons):
        ret = self.dc.tcwind_returnvalues(lats, lons, [100])
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) == len(lats)


    @pytest.mark.parametrize("lats,lons,status", [
        ([-17.6525, 30.6], [177.2634, -90.0], {'OK'}),
        ([0.0], [0.0], {'NO CONTENT'}),
        ([30.6], [-90.0], {'OK'}),
        ([35, 14.5],[-93.0, -76.8], {'OK', 'NO CONTENT'})
    ])
    def test_tcwind_status(self, lats, lons, status):
        ret = self.dc.tcwind_returnvalues(lats, lons, [100], terrain_correction='open_water')
        assert 'DeepCyc Maps' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)

        assert set(df.status) == status
        assert len(df) == len(lats)


    @pytest.mark.parametrize("scenario,time_horizon", [
        ('SSP1-2.6', 'now'),
        ('current_climate', '2035'),
        ('SSP1-2.6', '2035'),
        ('SSP2-4.5', '2035'),
        ('SSP5-8.5', '2035'),
        ('SSP1-2.6', '2050'),
        ('SSP2-4.5', '2050'),
        ('SSP5-8.5', '2050'),
        ('SSP1-2.6', '2065'),
        ('SSP2-4.5', '2065'),
        ('SSP5-8.5', '2065'),
    ])
    @pytest.mark.parametrize("min_lat,min_lon,location", [
        (-20.2, 148.97, 'Whitsunday Island'),
        (28.0, -82.5, 'Tampa'),
        (25.15, -80.735, 'Everglades'),
        (19.332, -155.757, 'Hawaii'),
        (13.07, 80.27, 'Chennai'),
        (35.6, 139.7, 'Tokyo')
    ])
    def test_tcwind_future_climate(self, scenario, time_horizon, min_lat, min_lon, location):

        if time_horizon == '2065' and location != 'Whitsunday Island':
            return

        lats, lons = generate_random_points(min_lat, min_lon)
        return_periods = [100]

        ret1 = self.dc.tcwind_returnvalues(lats, lons, return_periods,
                                             scenario='current_climate', time_horizon='now')
        assert 'DeepCyc Maps' in ret1['header']['product']
        assert ret1['header']['simulation_years'] == 41000
        df_now = gpd.GeoDataFrame.from_features(ret1)

        try:
            ret2 = self.dc.tcwind_returnvalues(lats, lons, return_periods,
                                                scenario=scenario, time_horizon=time_horizon)
        except Exception as e:
            assert scenario == 'current_climate' or time_horizon == 'now'
            assert 'Unsupported' in str(e)
        else:
            assert ret2['header']['scenario'] == scenario
            assert ret2['header']['time_horizon'] == time_horizon
            assert ret2['header']['simulation_years'] == 25000
            df_future = gpd.GeoDataFrame.from_features(ret2)

            assert (df_now.wind_speed < df_future.wind_speed).all()


    @pytest.mark.parametrize("num_points", [
        (1000),
    ])
    def test_tcwind_many_points(self, num_points):

        lats, lons = generate_random_points(27.5, -100, 33, -80, num_points)
        return_periods = [10, 25, 50, 100, 250, 500, 750]

        ret1 = self.dc.tcwind_returnvalues(lats, lons, return_periods,
                                            scenario='current_climate', time_horizon='now')
        assert 'DeepCyc Maps' in ret1['header']['product']
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
        lats, lons = generate_random_points(min_lat, min_lon, max_lat, max_lon, n_points)

        # Use the DeepCyc client to call the API
        ret = self.dc.tcwind_returnvalues(lats, lons, return_periods)
        assert 'DeepCyc Maps' in ret['header']['product']

        # Convert the results into a GeoPandas data frame
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) == len(lats) * len(return_periods)

        df_one = df[df.cell_id == df.iloc[0].cell_id]
        assert sorted(df_one.wind_speed) == list(df_one.wind_speed)
        assert list(df_one.return_period) == return_periods


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

    def test_tctrack_across_prime_meridian(self):
        """
        Test a query across the prime meridian
        """

        lats, lons = ([50, 50], [-1, 1])
        ret = self.dc.tctrack_events(lats, lons, 'line')
        df = gpd.GeoDataFrame.from_features(ret)

        # Expect hist to be small since it is not circling the globe
        assert len(df) < 500

        ret = self.dc.tctrack_events(50, -0.1, 'circle', radius_km=50)
        df = gpd.GeoDataFrame.from_features(ret)
        assert len(df) < 500


    def test_tctrack_max_polygon_size(self):
        """
        Test maximum radius limitation for tctrack circle query
        """

        ret = self.dc.tctrack_events(34, -84, 'circle', radius_km=180)
        assert 'DeepCyc Tracks' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)
        assert len(df) > 23000

        try:
            ret = self.dc.tctrack_events(34, -84, 'circle', radius_km=200)
        except Exception as e:
            err_msg = str(e)

        assert "API returned HTTP 400 with 'circle' radius" in err_msg

        lats, lons = ([29, 30, 30, 29, 29], [-91, -91, -90, -90, -91])
        ret = self.dc.tctrack_events(lats, lons, 'polygon')
        assert 'DeepCyc Tracks' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) > 14000

        try:
            lats, lons = ([24, 30, 30, 24, 24], [-92, -92, -87, -87, -92])
            ret = self.dc.tctrack_events(lats, lons, 'polygon')
        except Exception as e:
            err_msg = str(e)

        assert "API returned HTTP 400 with 'polygon' total area" in err_msg

        lats, lons = ([28, 28], [-100, -95])
        ret = self.dc.tctrack_events(lats, lons, 'line')
        assert 'DeepCyc Tracks' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) > 19000

        try:
            lats, lons = ([28, 28], [-100, -87])
            ret = self.dc.tctrack_events(lats, lons, 'line')
        except Exception as e:
            err_msg = str(e)

        assert "API returned HTTP 400 with 'line' total length" in err_msg

        try:
            lats, lons = ([24, 24.01, 24.01, 24, 24], [-100, -100, -80, -80, -100])
            ret = self.dc.tctrack_events(lats, lons, 'polygon')
        except Exception as e:
            err_msg = str(e)

        assert "API returned HTTP 400 with 'polygon' total perimiter" in err_msg


    @pytest.mark.parametrize("lat,lon", [
        (27.7221, -82.7386),
        (29.09915, -95.02722),
    ])
    def test_tctrack_central_pressure_circle(self, lat, lon):

        radius_km = 10
        ret_cp = self.dc.tctrack_central_pressure_events(lat, lon, 'circle', radius_km=radius_km)

        df_cp = gpd.GeoDataFrame.from_features(ret_cp)
        assert(list(df_cp.central_pressure)) == sorted(list(df_cp.central_pressure)), \
             'Central pressure not sorted'

        ret_vm = self.dc.tctrack_wind_speed_events(lat, lon, 'circle', radius_km=radius_km)
        df_vm = gpd.GeoDataFrame.from_features(ret_vm)

        assert (df_vm.wind_speed / df_cp.central_pressure).max() < 0.5, \
             'Unexpected wind - pressure relationship'
        assert (df_cp.central_pressure.loc[df_vm.wind_speed == 0] > 1000).all(),  \
             'Central pressure too low for given wind speed'

        assert set(df_vm.event_id) == set(df_cp.event_id), 'Inconsistent event ids'


    @pytest.mark.parametrize("lat,lon", [
        (27.7221, -82.7386), 
        (29.09915, -95.02722), 
        #(22.25, 114.20) # Hong Kong
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
        ([28.5, 28.5], [-88.5, -88.25]), # Gulf
        #([22.15, 22.15], [114.0, 114.25]) # Hong Kong
    ])
    def test_tctrack_line(self, lats, lons):
        ret = self.dc.tctrack_events(lats, lons, 'line')
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) > 1800

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
        assert 'DeepCyc Tracks' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df.wind_speed) == len(return_periods)


    @pytest.mark.parametrize("lats,lons,geometry,radius_km", [
        (27.366, -82.558, 'circle', 50),
        (-17.011, 178, 'circle', 50),
        ([25, 26], [-80, -80], 'line', None),
    ])
    def test_tctrack_compare_versions(self, lats, lons, geometry, radius_km):

        # tctrack events endpoint
        ret = self.dc_v206.tctrack_events(lats, lons, geometry, radius_km=radius_km)
        assert ret['header']['product'] == 'DeepCyc Tracks v2.0.6'
        assert ret['header']['simulation_years'] == 41000
        df_v206 = gpd.GeoDataFrame.from_features(ret)

        ret = self.dc_v207.tctrack_events(lats, lons, geometry, radius_km=radius_km)
        assert ret['header']['product'] == 'DeepCyc Tracks v2.0.7'
        assert ret['header']['simulation_years'] == 41000
        df_v207 = gpd.GeoDataFrame.from_features(ret)

        assert (df_v206 == df_v207).all().all()
        assert sorted(df_v207.year_id)[0].split('_')[0] == '1980'
        assert sorted(df_v207.year_id)[-1].split('_')[0] == '2020'

        ret = self.dc_v208.tctrack_events(lats, lons, geometry, radius_km=radius_km)
        assert ret['header']['product'] == 'DeepCyc Tracks v2.0.8'
        assert ret['header']['simulation_years'] == 66000
        df_v208 = gpd.GeoDataFrame.from_features(ret)

        assert set(df_v206.event_id).issubset(df_v208.event_id)
        assert sorted(df_v208.year_id)[0].split('_')[0] == '1980'
        assert sorted(df_v208.year_id)[-1].split('_')[0] == '2023'

        # tctrack returnvalues endpoint
        ret = self.dc_v207.tctrack_returnvalues(lats, lons, [100, 200, 250, 500, 1000, 2000], geometry,
                                            radius_km=radius_km)
        df_v207 = gpd.GeoDataFrame.from_features(ret)
        ret = self.dc_v208.tctrack_returnvalues(lats, lons, [100, 200, 250, 500, 1000, 2000], geometry,
                                            radius_km=radius_km)
        df_v208 = gpd.GeoDataFrame.from_features(ret)

        # Expect less than a 6% difference in return values between the versions
        assert ((abs(df_v207.wind_speed - df_v208.wind_speed) / df_v208.wind_speed) < 0.06).all()


    @pytest.mark.parametrize("lats,lons,geometry,radius_km", [
        (26, -81, 'circle', 2),
        (27.366, -82.558, 'circle', 20),
        ([29.75, 30, 30, 29.75, 29.75], [-91, -91, -90.75, -90.75, -91], 'polygon', None),
    ])
    def test_tcwind_eventstats(self, lats, lons, geometry, radius_km):

        ret = self.dc.tcwind_eventstats(lats, lons, geometry, radius_km=radius_km)
        df = gpd.GeoDataFrame.from_features(ret)

        # All event ids are unique
        assert len(set(df.event_id)) == len(df.event_id)

        # geometry is in the middle of a cell
        rkg_res = 2**-7 + 2**-9
        top_lat = df.iloc[0].geometry.y
        top_lon = df.iloc[0].geometry.x
        assert (top_lat / rkg_res) % 1 == 0.5
        assert (top_lon / rkg_res) % 1 == 0.5

        # Check the wind speed
        ret = self.dc.tcwind_events(top_lat, top_lon)
        chk_df = gpd.GeoDataFrame.from_features(ret)

        top_ws = df.iloc[0].max_wind_speed
        top_event_id = df.iloc[0].event_id
        assert chk_df[chk_df.event_id == top_event_id].wind_speed.item() == top_ws


    @pytest.mark.parametrize("min_lat,max_lat,min_lon,max_lon,n_points,return_periods,label", [
        (-20,-15,175,179, 10, [10,100,500,1000], 'Fiji'),
        (-15,-12.5,-175,-170, 10, [10,100,500,1000], 'Samoa'),
        (-16.975,-16.90,179.95,180, 10, [10,100,500,1000], 'Taveuni_Island')
    ])
    def test_tcwind_compare_versions(self, min_lat, max_lat, min_lon, max_lon, n_points, return_periods, label):
        # Creates sample points
        lats, lons = generate_random_points(min_lat, min_lon, max_lat, max_lon, n_points)

        ret = self.dc_v206.tcwind_returnvalues(lats, lons, return_periods)
        assert ret['header']['product'] == 'DeepCyc Maps v2.0.6'
        assert ret['header']['simulation_years'] == 41000
        df_v206 = gpd.GeoDataFrame.from_features(ret)

        ret = self.dc_v207.tcwind_returnvalues(lats, lons, return_periods)
        assert ret['header']['product'] == 'DeepCyc Maps v2.0.7'
        assert ret['header']['simulation_years'] == 41000
        df_v207 = gpd.GeoDataFrame.from_features(ret)

        assert (df_v206 == df_v207).all().all()

        ret = self.dc_v208.tcwind_returnvalues(lats, lons, return_periods)
        assert ret['header']['product'] == 'DeepCyc Maps v2.0.8'
        assert ret['header']['simulation_years'] == 66000
        df_v208 = gpd.GeoDataFrame.from_features(ret)

        if label == 'Taveuni_Island':
            # The newest version has terrain fixes in this limited region
            assert (abs(df_v207.wind_speed - df_v208.wind_speed) / df_v208.wind_speed).max() > 0.1
        else:
            # Expect less than a 5% difference in return values between the versions
            assert ((abs(df_v207.wind_speed - df_v208.wind_speed) / df_v208.wind_speed) < 0.05).all()


    @pytest.mark.parametrize("scenario,time_horizon", [
        ('current_climate', 'now'),
        ('SSP1-2.6', '2035'),
        ('SSP1-2.6', '2050'),
        ('SSP1-2.6', '2065'),
        ('SSP2-4.5', '2035'),
        ('SSP2-4.5', '2050'),
        ('SSP2-4.5', '2065'),
        ('SSP5-8.5', '2035'),
        ('SSP5-8.5', '2050'),
        ('SSP5-8.5', '2065'),

        ('SSP1-2.6', '2080'),
        ('SSP2-4.5', '2080'),
        ('SSP5-8.5', '2080'),
    ])
    @pytest.mark.parametrize("lats,lons", [
        ([28.5, 28.5], [-88.5, -88.25]), # Gulf
        ([22.15, 22.15], [114.0, 114.25]) # Hong Kong
    ])
    def test_tctrack_future_climate(self, lats, lons, scenario, time_horizon):

        return_periods = [50, 100, 250, 500, 1000]
        ret = self.dc.tctrack_returnvalues(lats, lons, return_periods, 'line',
                                           scenario=scenario, time_horizon=time_horizon)
        assert 'DeepCyc Tracks' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)
        assert len(df) == 5
        assert ret['header']['scenario'] == scenario
        assert ret['header']['time_horizon'] == time_horizon

        # FIXME: add 2080 time_horizon
        if time_horizon in ['2080']:
            set(df.status) == {'NO CONTENT'}
        else:
            set(df.status) == {'OK'}
            assert list(df.wind_speed) == sorted(list(df.wind_speed))

            if scenario == 'current_climate':
                assert ret['header']['simulation_years'] == 41000
            else:
                assert ret['header']['simulation_years'] == 25000


    def test_tctrack_returnvalues_polygon_geojson(self):
        """
        Use a GeoJSON file to query deepcyc tctracks

        The example file was manually created using: https://geojson.io
        """

        return_periods = [50, 100, 250, 500]

        input_df = gpd.read_file(Path(__file__).parent / 'florida.geojson')

        assert isinstance(input_df.iloc[0].geometry,
                            shapely.geometry.polygon.Polygon), \
                'Unexpected shape in GeoJSON'

        lons, lats = input_df.iloc[0].geometry.boundary.coords.xy
        lons = lons.tolist()
        lats = lats.tolist()

        ret = self.dc.tctrack_returnvalues(lats, lons, return_periods, 'polygon')
        df = gpd.GeoDataFrame.from_features(ret)

        assert (df.status == 'OK').all()
