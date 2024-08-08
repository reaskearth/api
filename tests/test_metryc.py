import logging
import time
import pandas as pd
import datetime as dt
import geopandas as gpd
import numpy as np
import pytest
import shapely
import json
import geopy
import geopy.distance
import sys

from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.metryc import Metryc

from test_deepcyc import generate_random_points

class TestMetryc():
    mc = Metryc()

    lats = [29.95747]
    lons = [-90.06295]

    logger = logging.getLogger(__name__)


    @pytest.mark.parametrize("lats,lons,storm_name", [
        ([26.95747, 25.0], [-82.06295, -82.1], 'Katrina'),
        ([-16.5856], [178.898], 'Yasa'),
        ([-20.2264804], [169.7780007], 'Yali')
    ])
    def test_tcwind_simple(self, lats, lons, storm_name):
        ret = self.mc.tcwind_events(lats, lons)
        df = gpd.GeoDataFrame.from_features(ret)

        assert storm_name in list(df.storm_name)

    @pytest.mark.parametrize("lats,lons,status", [
        ([-17.6525, 30.6], [177.2634, -90.0], {'OK'}),
        ([30, 24.0],[-93.0, -93.0], {'OK', 'NO CONTENT'}),
        ([24.0], [-93.0], {'NO CONTENT'}),
        ([30.6], [-90.0], {'OK'}),
    ])
    def test_tcwind_status(self, lats, lons, status):

        ret = self.mc.tcwind_events(lats, lons, terrain_correction='open_water')
        df = gpd.GeoDataFrame.from_features(ret)
        df['query_geometry'] = df.apply(lambda x: shapely.from_geojson(json.dumps(x.query_geometry)), axis=1)

        assert set(df.query_geometry.x) == set(lons)
        assert set(df.query_geometry.y) == set(lats)
        assert set(df.status) == status


    @pytest.mark.parametrize("lats,lons,storm_name", [
        ([29.95747], [-90.06295], 'Katrina')
    ])
    def test_tcwind_terrain_correction(self, lats, lons, storm_name):

        for terrain_correction in ['open_water', 'open_terrain', 'full_terrain_gust']:
            ret = self.mc.tcwind_events(lats, lons, terrain_correction=terrain_correction)
            assert ret['header']['terrain_correction'] == terrain_correction

            df = gpd.GeoDataFrame.from_features(ret)
            assert storm_name in list(df.storm_name)


    @pytest.mark.parametrize("width_and_height,lower_lat,left_lon", [
        (10, 28, -82),
    ])
    def test_tcwind_small_region(self, width_and_height, lower_lat, left_lon):

        res = 2**-7 + 2**-9
        lats = [lower_lat + i*res for i in range(width_and_height)]
        lons = [left_lon + i*res for i in range(width_and_height)]

        yy, xx = np.meshgrid(lats, lons)

        ret = self.mc.tcwind_events(yy.flatten(), xx.flatten())
        assert 'Metryc Historical' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(set(df.cell_id)) == width_and_height*width_and_height


    @pytest.mark.parametrize("lats,lons,geometry,radius_km", [
        ([30], [-90], 'circle', 50),
        (30, -90, 'circle', 50),
        ([28, 27.5, 25, 25, 27.5, 30], [-83, -83, -81.5, -79.5, -79.5, -80], 'line', None)
    ])
    def test_tctrack_events(self, lats, lons, geometry, radius_km):
        """
        Test Metryc endpoint to guery by geometry
        """

        ret = self.mc.tctrack_events(lats, lons, geometry, radius_km=radius_km)
        df = gpd.GeoDataFrame.from_features(ret)

        assert 'query_geometry' in ret['header']
        geom = shapely.from_geojson(json.dumps(ret['header']['query_geometry']))

        if geometry == 'circle':
            lons, lats = geom.exterior.coords.xy
            diameter = (np.max(lons) - np.min(lons)) * np.cos(np.deg2rad(np.mean(lats)))*111
            assert (1 - (diameter / (2*radius_km))) < 0.01
        elif geometry == 'line':
            query_lons = shapely.get_coordinates(geom)[:, 0]
            query_lats = shapely.get_coordinates(geom)[:, 1]

            # FIXME: check this properly
            assert set(lats) == set(query_lats)
            assert set(lons) == set(query_lons)

        assert len(df) > 30


    def test_circle_intersection(self):
        """
        Test to see whether API is reporting circle to track intersection properly
        """

        radius_km = 10

        track_point = geopy.Point(30.27, -89.60)
        clat, clon, _ = geopy.distance.distance(radius_km).destination(track_point, 90)

        clat = 30.27
        clon = -89.70
        ret = self.mc.tctrack_events([clat], [clon], geometry='circle', radius_km=radius_km)
        assert 'Metryc Historical' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)

        assert 'Katrina' in list(df.storm_name)

        geom = df.iloc[0].geometry
        ilat = geom.y
        ilon = geom.x

        dist = geopy.distance.geodesic((clat, clon), (ilat, ilon))
        assert abs(1 - (dist.km / radius_km)) < 1e-4


    def test_live_list(self):
        """
        Get listing of all live / in-season storms
        """

        ret = self.mc.live_tcwind_list()
        assert 'Metryc Live' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)

        assert 'Otis_2023_2023291N08267_Live_USA_EP' in list(df.event_id)
        assert len(df) >= 1


    def test_historical_list(self):
        """
        Get listing of all historical storms
        """

        ret = self.mc.historical_tcwind_list()
        assert 'Metryc Historical' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df.event_id) == len(set(df.event_id))
        assert len(df) > 800


    def test_list_with_agency(self):

        ret = self.mc.historical_tcwind_list()
        assert 'Metryc Historical' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)

        agencies = set([e.split('_')[4] for e in list(df.event_id)])
        assert len(agencies) > 1

        for agency in agencies:
            ret = self.mc.historical_tcwind_list(agency=agency)
            df = gpd.GeoDataFrame.from_features(ret)
            assert set([e.split('_')[4] for e in list(df.event_id)]) == {agency}

        # Select an invalid agency
        try:
            ret = self.mc.historical_tcwind_list(agency='INVALID')
        except Exception as e:
            assert 'HTTP 422' in str(e)


    @pytest.mark.parametrize("agency", [
        'USA',
        'BOM',
        'TOKYO'
    ])
    def test_footprint_with_agency(self, agency):
        """
        Get footprint of a live storm
        """

        ret = self.mc.historical_tcwind_list(agency=agency)
        df = gpd.GeoDataFrame.from_features(ret)

        row = df.iloc[0]
        min_lon, min_lat, max_lon, max_lat = row.geometry.bounds

        ret = self.mc.historical_tcwind_footprint(min_lat, max_lat, min_lon, max_lon,
                                                  storm_name=row.storm_name,
                                                  storm_year=row.storm_year, agency=agency,
                                                  format='geojson')
        df = gpd.GeoDataFrame.from_features(ret)
        import pdb
        pdb.set_trace()



    @pytest.mark.parametrize("product", [
        'Live',
        'Historical'
    ])
    def test_footprint(self, product):
        """
        Get footprint of a live storm
        """

        if product == 'Live':
            ret = self.mc.live_tcwind_list()
        else:
            ret = self.mc.historical_tcwind_list()

        assert product in ret['header']['product']

        df = gpd.GeoDataFrame.from_features(ret)
        row = df.iloc[0]
        min_lon, min_lat, max_lon, max_lat = row.geometry.bounds

        if product == 'Live':
            ret = self.mc.live_tcwind_footprint(min_lat, max_lat, min_lon, max_lon,
                                                storm_name=row.storm_name,
                                                storm_year=row.storm_year, format='geojson')
            assert 'Metryc Live' in ret['header']['product']
            assert len(ret['features']) >= 1
        else:
            ret = self.mc.historical_tcwind_footprint(min_lat, max_lat, min_lon, max_lon,
                                                      storm_name=row.storm_name,
                                                      storm_year=row.storm_year, format='geojson')
            assert 'Metryc Historical' in ret['header']['product']
            assert len(ret['features']) > 1000

        assert ret['header']['storm_name'] == storm_name
        assert int(ret['header']['storm_year']) == storm_year

    def test_tctrack_points(self):

        ret = self.mc.historical_tctrack_points(storm_id='1994197N09229')
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) == 73
        assert df.iloc[0].track_name == 'Emilia 1994'

        ret = self.mc.historical_tctrack_points(storm_id='2017228N14314')
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) == 141
        assert df.iloc[0].track_name == 'Harvey 2017'
        assert round(df.wind_speed.max()) == 213

        try:
            ret = self.mc.historical_tctrack_points(storm_id='INVALID_STORM_ID')
        except Exception as e:
            assert 'storm_id INVALID_STORM_ID not found' in str(e)


    def test_tctrack_consistency(self):
        """
        Test consistency of storm track year and name
        """

        ret = self.mc.historical_tcwind_list()
        assert 'Metryc Historical' in ret['header']['product']
        df = gpd.GeoDataFrame.from_features(ret)

        storm_names = [sn.split('_')[0] for sn in df.event_id]
        assert (df.storm_name == storm_names).all(), 'Storm names do not match'

        storm_years = [int(sn.split('_')[1]) for sn in df.event_id]
        assert (df.storm_year == storm_years).all(), 'Storm years do not match'

        for sid, storm_name, storm_year in zip(df.storm_id, storm_names, storm_years):
            try:
                ret = self.mc.historical_tctrack_points(storm_id=sid)
            except Exception as e:
                continue

            # FIXME: inconsistencies to be fixed
            if (storm_name == 'Bonita' and storm_year == 1996) or \
               (storm_name == 'Bernie' and storm_year == 2001) or \
               (storm_name == 'Christelle' and storm_year == 1994):
                continue

            points_storm_name = ret['header']['storm_name']
            points_storm_year = int(ret['header']['storm_year'])

            # FIXME: remove the .lower() - these should be case sensitive
            assert points_storm_name.lower() == storm_name.lower(), \
                'storm name inconsistent {} {} != {} {}'.format(points_storm_name, points_storm_year, storm_name, storm_year)

            assert points_storm_year == storm_year, \
                'storm year inconsistent {} {} != {}'.format(storm_name, points_storm_year, storm_year)

            start_time = gpd.GeoDataFrame.from_features(ret).iloc[0].iso_time
            year = dt.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ').year

            assert year == storm_year, 'storm_year wrong for {} {}'.format(storm_name, storm_year)


    def test_circle_perf(self):
        """
        Test the events endpoint performance
        """

        accurate_runtimes = []
        fast_runtimes = []
        num_events = []
        lats, lons = generate_random_points(30.2, -89.7, n_points=101)

        for i, (lat, lon) in enumerate(zip(lats, lons)):
            start_time = time.time()
            ret = self.mc.tctrack_events(lat, lon, geometry='circle', radius_km=50)
            assert ret['header']['map_projection_used_for_geometric_calculations'] == 'AEQD'
            if i != 0:
               accurate_runtimes.append(time.time() - start_time)

            start_time = time.time()
            ret = self.mc.tctrack_events(lat, lon, geometry='circle', radius_km=50, accurate_flag=False)
            assert ret['header']['map_projection_used_for_geometric_calculations'] == 'WGS84'
            if i != 0:
               fast_runtimes.append(time.time() - start_time)

            df = gpd.GeoDataFrame.from_features(ret)
            num_events.append(len(df))

        print('metrcy/events events min {}, max {}'.format(np.min(num_events), np.max(num_events)))

        print('metrcy/events accurate time min {}s, max {}s, mean {}s, stddev {}s'.format(np.min(accurate_runtimes), 
                    np.max(accurate_runtimes), np.mean(accurate_runtimes), np.std(accurate_runtimes)))
        print('metrcy/events fast time min {}s, max {}s, mean {}s, stddev {}s'.format(np.min(fast_runtimes), 
                    np.max(fast_runtimes), np.mean(fast_runtimes), np.std(fast_runtimes)))

        # This does not work under high load
        #assert np.mean(fast_runtimes) < np.mean(accurate_runtimes)
