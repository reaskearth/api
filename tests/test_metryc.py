import logging
import pandas as pd
import geopandas as gpd
import pytest
import sys

from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.metryc import Metryc

class TestMetryc():
    mc = Metryc()

    lats = [29.95747]
    lons = [-90.06295]

    logger = logging.getLogger(__name__)

    def validate_point_results(self, terrain_correction, windspeed_averaging_period, results):
        """
        Helper to perform validation of common attributes of the Point API results
        """
        # TODO: replace by jsonschema validation?
        assert results is not None, "API call returned no results"
        assert 'features' in results
        assert 'geometry' in results['features'][0]
        assert 'geometry' in results['features'][0]
        assert 'coordinates' in results['features'][0]['geometry']
        assert 'type' in results['features'][0]['geometry']
        assert 'properties' in results['features'][0]
        assert 'cell_id' in results['features'][0]['properties']
        assert 'latitude' in results['features'][0]['properties']
        assert 'longitude' in results['features'][0]['properties']
        assert 'storm_names' in results['features'][0]['properties']
        assert 'storm_seasons' in results['features'][0]['properties']
        assert 'windspeeds' in results['features'][0]['properties']
        assert 'storm_seasons' in results['features'][0]['properties']
        assert 'type' in results['features'][0]
        assert 'Feature' in results['features'][0]['type']
        assert 'header' in results
        assert 'product' in results['header']
        assert 'reporting_period' in results['header']
        assert 'terrain_correction' in results['header']
        assert 'units' in results['header']
        assert 'windspeed_averaing_period' in results['header']
        assert 'type' in results
        assert 'FeatureCollection' in results['type']
        assert 'kph' in results['header']['units']

        assert terrain_correction in results['header']['terrain_correction'], f"terrain_correction in header does not match '{terrain_correction}' "
        assert windspeed_averaging_period in results['header']['windspeed_averaing_period'], f"windspeed averaging period does not match '{windspeed_averaging_period}'"


    @pytest.mark.parametrize("lats,lons,name", [
        ([29.95747], [-90.06295], 'Katrina')
    ])
    def test_tcwind_simple(self, lats, lons, name):
        ret = self.mc.tcwind_events(lats, lons)
        df = gpd.GeoDataFrame.from_features(ret)

        assert name in list(df.name)

        
    @pytest.mark.parametrize("epoch, terrain_correction, windspeed_averaging_period", [
        ('Present_Day', 'FT_GUST', '3-seconds'),
        ('Present Day', 'OW', '1-minute'),
        ('Present_Day', 'OT', '1-minute')
    ])
    def test_tcwind_events(self, epoch, terrain_correction, windspeed_averaging_period):
        """
        Test Metryc endpoint to query by point
        """
        return
        print(f"epoch='{epoch}', terrain_correction='{terrain_correction}', windspeed_averaging_period='{windspeed_averaging_period}'")
        results = self.mc.tcwind_events(self.lats, self.lons, epoch, terrain_correction, windspeed_averaging_period)

        self.validate_point_results(terrain_correction, windspeed_averaging_period, results)
    

    def test_emily_1987(self):
        """
        Test windspeeds for Emily 1987
        """
        lats = [18.2369, 18.2369, 18.2369, 18.2369, 18.2369, 18.2369, 18.2369,
            18.2273, 18.2273, 18.2273, 18.2273, 18.2273, 18.2273, 18.2273]
        lons = [-70.2883, -70.2786, -70.2680, -70.2584, -70.2484, -70.2352, -70.2289,
            -70.2883, -70.2786, -70.2680, -70.2584, -70.2484, -70.2352, -70.2289]

        return

        ret = self.mc.tcwind_events(lats, lons)
        df = gpd.GeoDataFrame.from_features(ret).set_index('cell_id')

        for i, val in enumerate([210, 181, 207, 181, 180, 179,
            178, 213, 211, 210, 208, 192, 199, 189]):
            
            storm_name_season = ['{}_{}'.format(n, s) for n, s in \
                zip(df.iloc[i].storm_names, df.iloc[i].storm_seasons)]
            
            idx = storm_name_season.index('Emily_1987')

            assert df.iloc[i].windspeeds[idx] == val
    
    @pytest.mark.parametrize("lats,lons,gate,radius,tag", [
        ([30], [-90], 'circle', 50, 'New Orleans'),
        (30, -90, 'circle', 50, 'New Orleans'),
        ([28, 27.5, 25, 25, 27.5, 30], [-83, -83, -81.5, -79.5, -79.5, -80], 'line', None, 'Florida')
    ])
    def test_twtrack_events(self, lats, lons, gate, radius, tag):
        """
        Test Metryc endpoint to guery by gate
        """
        return

        results = self.mc.tctrack_events(lats, lons, gate, radius, tag)

        assert results is not None