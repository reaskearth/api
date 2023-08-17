import logging
import pandas as pd
import geopandas as gpd
import numpy as np
import pytest
import shapely
import json
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


    @pytest.mark.parametrize("lats,lons,expected_storm_count", [
        ([30.01], [-90.01], 45), # Gulf of Mexico
        ([25.0], [-81.0], 51), # Florida South
        ([32.5], [-80.0], 42), # Carolinas
        ([21.0], [-88.0], 16), # Yucatan
    ])
    def test_tcwind_coverage(self, lats, lons, expected_storm_count):
        ret = self.mc.tcwind_events(lats, lons)
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) == expected_storm_count


    @pytest.mark.parametrize("lats,lons,name,year,ft_gust,ow_1min,ot_1min", [
        #([13.5], [123.5], 'Rammasun', 2014, ),  
        #([13.5], [123.5], 'Angela', 1995),  
        ([30.415], [-89.222], 'Katrina', 2005, 170, 165, 147),  
    ])
    def test_tcwind_values(self, lats, lons, name, year, ft_gust, ow_1min, ot_1min):
        """
        Test Phillipines wind footprints
        """

        ret = self.mc.tcwind_events(lats, lons)
        assert ret['header']['terrain_correction'] == 'full_terrain_gust'
        assert ret['header']['wind_speed_averaging_period'] == '3_seconds'
        df = gpd.GeoDataFrame.from_features(ret)

        ft = df[(df.name == name) & (df.year == year)].iloc[0].wind_speed 
        assert round(ft) == ft_gust

        ret = self.mc.tcwind_events(lats, lons, terrain_correction='open_water', wind_speed_averaging_period='1_minute')
        assert ret['header']['terrain_correction'] == 'open_water'
        assert ret['header']['wind_speed_averaging_period'] == '1_minute'
        df = gpd.GeoDataFrame.from_features(ret)

        ow = df[(df.name == name) & (df.year == year)].iloc[0].wind_speed 
        assert round(ow) == ow_1min

        ret = self.mc.tcwind_events(lats, lons, terrain_correction='open_terrain', wind_speed_averaging_period='1_minute')
        assert ret['header']['terrain_correction'] == 'open_terrain'
        assert ret['header']['wind_speed_averaging_period'] == '1_minute'
        df = gpd.GeoDataFrame.from_features(ret)

        ot = df[(df.name == name) & (df.year == year)].iloc[0].wind_speed 
        assert round(ot) == ot_1min


    def test_emily_1987(self):
        """
        Test windspeeds for Emily 1987
        """
        lats = [18.2369, 18.2369, 18.2369, 18.2369, 18.2369, 18.2369, 18.2369,
            18.2273, 18.2273, 18.2273, 18.2273, 18.2273, 18.2273, 18.2273]
        lons = [-70.2883, -70.2786, -70.2680, -70.2584, -70.2484, -70.2352, -70.2289,
            -70.2883, -70.2786, -70.2680, -70.2584, -70.2484, -70.2352, -70.2289]

        ret = self.mc.tcwind_events(lats, lons)
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df.cell_id.unique()) == len(lats)

        expected_ws = [210, 181, 207, 181, 180, 179, 178, 213, 211, 210, 208, 192, 199, 189]
        assert list(df[(df.name == 'Emily') & (df.year == 1987)].wind_speed) == expected_ws


    @pytest.mark.parametrize("width_and_height,lower_lat,left_lon", [
        (10, 27.5, -83),
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


    @pytest.mark.skip(reason='FIXME: update github secrets to contain limited permission test user')
    @pytest.mark.parametrize("lats,lons", [
        ([29.95747], [-90.06295])
    ])
    def test_tcwind_noperms(self, lats, lons):

        tmp_mc = Metryc(config_section='hamilton_island')
        try:
            ret = tmp_mc.tcwind_events(lats, lons)
            assert False, 'Should not get here'
        except Exception as e:
            assert '403' in str(e)