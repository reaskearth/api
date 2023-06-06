import logging
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

        
    @pytest.mark.parametrize("epoch, terrain_correction, windspeed_averaging_period", [
        ('Present_Day', 'FT_GUST', '3-seconds'),
        ('Present Day', 'OW', '1-minute'),
        ('Present_Day', 'OT', '1-minute')
    ])
    def test_point(self, epoch, terrain_correction, windspeed_averaging_period):
        """
        Test Metryc endpoint to query by point
        """
        print(f"epoch='{epoch}', terrain_correction='{terrain_correction}', windspeed_averaging_period='{windspeed_averaging_period}'")
        results = self.mc.point(self.lats, self.lons, epoch, terrain_correction, windspeed_averaging_period)

        self.validate_point_results(terrain_correction, windspeed_averaging_period, results)
    
    @pytest.mark.parametrize("lats,lons,gate,radius,tag", [
        ([30], [-90], 'circle', 50, 'New Orleans'),
        (30, -90, 'circle', 50, 'New Orleans'),
        ([28, 27.5, 25, 25, 27.5, 30], [-83, -83, -81.5, -79.5, -79.5, -80], 'line', None, 'Florida')
    ])
    def test_gate(self, lats, lons, gate, radius, tag):
        """
        Test Metryc endpoint to guery by gate
        """
        results = self.mc.gate(lats, lons, gate, radius, tag)

        assert results is not None
    

    @pytest.mark.parametrize("bbox", [
        ({'min_lat': 27.0, 'max_lat': 28.0, 'min_lon': -83.0, 'max_lon': -82.0}) # Tampa/FL
    ])
    def test_collections(self, bbox):
        """
        Test Metryc endpoint to query by bounding box
        """
        results = self.mc.collections(bbox)

        assert results is not None