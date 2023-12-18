import logging
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


class TestMetryc():
    mc = Metryc()

    lats = [29.95747]
    lons = [-90.06295]

    logger = logging.getLogger(__name__)


    @pytest.mark.parametrize("lats,lons,name", [
        ([29.95747], [-90.06295], 'Katrina')
    ])
    def test_tcwind_simple(self, lats, lons, name):
        ret = self.mc.tcwind_events(lats, lons)
        df = gpd.GeoDataFrame.from_features(ret)

        assert name in list(df.name)

    @pytest.mark.parametrize("lats,lons,status", [
        ([-17.6525, 30.6], [177.2634, -90.0], {'OK', 'NO CONTENT'}),
        ([24.0], [-93.0], {'NO CONTENT'}),
        ([30.6], [-90.0], {'OK'}),
        ([30, 24.0],[-93.0, -93.0], {'OK', 'NO CONTENT'})])
    def test_tcwind_status(self, lats, lons, status):

        ret = self.mc.tcwind_events(lats, lons, terrain_correction='open_water')
        df = gpd.GeoDataFrame.from_features(ret)

        assert set(df.status) == status


    @pytest.mark.parametrize("lats,lons,name", [
        ([29.95747], [-90.06295], 'Katrina')
    ])
    def test_tcwind_terrain_correction(self, lats, lons, name):

        for terrain_correction in ['open_water', 'open_terrain', 'full_terrain_gust']:
            ret = self.mc.tcwind_events(lats, lons, terrain_correction=terrain_correction)
            assert ret['header']['terrain_correction'] == terrain_correction

            df = gpd.GeoDataFrame.from_features(ret)
            assert name in list(df.name)


    @pytest.mark.parametrize("width_and_height,lower_lat,left_lon", [
        (10, 28, -82),
    ])
    def test_tcwind_small_region(self, width_and_height, lower_lat, left_lon):

        res = 2**-7 + 2**-9
        lats = [lower_lat + i*res for i in range(width_and_height)]
        lons = [left_lon + i*res for i in range(width_and_height)]

        yy, xx = np.meshgrid(lats, lons)

        ret = self.mc.tcwind_events(yy.flatten(), xx.flatten())
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
        df = gpd.GeoDataFrame.from_features(ret)

        assert 'Katrina' in list(df.name)

        geom = df.iloc[0].geometry
        ilat = geom.y
        ilon = geom.x

        dist = geopy.distance.geodesic((clat, clon), (ilat, ilon))
        assert abs(1 - (dist.km / radius_km)) < 1e-4

    @pytest.mark.parametrize("min_lat,max_lat,min_lon,max_lon,storm_name,storm_season,terrain_correction,wind_speed_averaging_period,samples", [
        (29.68, 30.13, -90.32, -89.78, 'Katrina', 2005, 'full_terrain_gust', '3_seconds', 5),
        (29.68, 30.13, -90.32, -89.78, 'Katrina', 2005, 'open_water', '1_minute', 5),
        (29.68, 30.13, -90.32, -89.78, 'Katrina', 2005, 'open_terrain', '1_minute', 5),
        (11.11, 11.44, 124.5, 125, 'Haiyan', 2013, 'full_terrain_gust', '3_seconds', 5),
        (11.11, 11.44, 124.5, 125, 'Haiyan', 2013, 'open_water', '1_minute', 5),
        (11.11, 11.44, 124.5, 125, 'Haiyan', 2013, 'open_terrain', '1_minute', 5),

    ])
    def test_tcwind_crosscheck(self, min_lat, max_lat, min_lon, max_lon, storm_name, storm_season, terrain_correction, wind_speed_averaging_period, samples):
        """
        Compare TC wind values returning from TC Wind events and footprint endpoints
        """
        ret = self.mc.tcwind_footprint(min_lat, max_lat, min_lon, max_lon, storm_name=storm_name, storm_season=storm_season, terrain_correction=terrain_correction, wind_speed_averaging_period=wind_speed_averaging_period)

        # get random samples from the footprint
        df = gpd.GeoDataFrame.from_features(ret)
        df = df.sample(samples)

        # calculate center of each geometry
        df['center'] = df.geometry.centroid

        # iterate over data frame calling the events endpoint
        for i, row in df.iterrows():
            ret2 = self.mc.tcwind_events(row.center.y, row.center.x, terrain_correction=terrain_correction, wind_speed_averaging_period=wind_speed_averaging_period)
            df2 = gpd.GeoDataFrame.from_features(ret2)
            df2 = df2[(df2.name == storm_name) & (df2.year == storm_season)]

            # ensure there's a single match from the tcwind events endpoint response
            assert df2.shape[0] == 1

            # check that the wind speed is the same
            assert df2.iloc[0].wind_speed == row.wind_speed
