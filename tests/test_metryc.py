import logging
import time
import pandas as pd
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
        ([29.95747], [-90.06295], 'Katrina')
    ])
    def test_tcwind_simple(self, lats, lons, storm_name):
        ret = self.mc.tcwind_events(lats, lons)
        df = gpd.GeoDataFrame.from_features(ret)

        assert storm_name in list(df.storm_name)

    @pytest.mark.parametrize("lats,lons,status", [
        ([-17.6525, 30.6], [177.2634, -90.0], {'OK'}),
        ([24.0], [-93.0], {'NO CONTENT'}),
        ([30.6], [-90.0], {'OK'}),
        ([30, 24.0],[-93.0, -93.0], {'OK', 'NO CONTENT'})])
    def test_tcwind_status(self, lats, lons, status):

        ret = self.mc.tcwind_events(lats, lons, terrain_correction='open_water')
        df = gpd.GeoDataFrame.from_features(ret)

        assert set(['geometry', 'cell_id', 'storm_name', 'storm_year',
                    'wind_speed', 'storm_id', 'event_id', 'status']) == set(df.columns)

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
        ([50], [-90], 'circle', 10),
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

        if len(df) > 0:
            set(['geometry', 'storm_name', 'storm_year',
                 'wind_speed', 'storm_id', 'event_id']) == set(df.columns)
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

        assert len(df) > 800


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
        min_lon, min_lat, max_lon, max_lat = df.iloc[0].geometry.bounds
        storm_name = df.iloc[0].storm_name
        storm_year = df.iloc[0].storm_year

        row = df.iloc[0]
        min_lon, min_lat, max_lon, max_lat = row.geometry.bounds

        if product == 'Live':
            ret = self.mc.live_tcwind_footprint(min_lat, max_lat, min_lon, max_lon,
                                                storm_name=row.storm_name,
                                                storm_year=row.storm_year)
            assert 'Metryc Live' in ret['header']['product']
            assert len(ret['features']) >= 1
        else:
            ret = self.mc.historical_tcwind_footprint(min_lat, max_lat, min_lon, max_lon,
                                                      storm_name=row.storm_name,
                                                      storm_year=row.storm_year)
            assert 'Metryc Historical' in ret['header']['product']
            assert len(ret['features']) > 1000

        assert ret['header']['storm_name'] == storm_name
        assert ret['header']['storm_year'] == storm_year
