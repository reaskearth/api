import sys
import unittest

from pathlib import Path

from test_setup import TestSetup

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.metryc import Metryc

class TestMetryc(TestSetup):
    mc = Metryc()

    lats = [29.95747]
    lons = [-90.06295]

    def validate_point_results(self, results):
        # TODO: replace by jsonschema validation?
        self.assertIsNotNone(results)
        self.assertIn('features', results)
        self.assertIn('geometry', results['features'][0])
        self.assertIn('coordinates', results['features'][0]['geometry'])
        self.assertIn('type', results['features'][0]['geometry'])
        self.assertIn('properties', results['features'][0])
        self.assertIn('cell_id', results['features'][0]['properties'])
        self.assertIn('latitude', results['features'][0]['properties'])
        self.assertIn('longitude', results['features'][0]['properties'])
        self.assertIn('storm_names', results['features'][0]['properties'])
        self.assertIn('storm_seasons', results['features'][0]['properties'])
        self.assertIn('windspeeds', results['features'][0]['properties'])
        self.assertIn('storm_seasons', results['features'][0]['properties'])
        self.assertIn('type', results['features'][0])
        self.assertEqual('Feature', results['features'][0]['type'])
        self.assertIn('header', results)
        self.assertIn('product', results['header'])
        self.assertIn('reporting_period', results['header'])
        self.assertIn('terrain_correction', results['header'])
        self.assertIn('units', results['header'])
        # TODO: fix keyword upstream
        self.assertIn('windspeed_averaing_period', results['header'])
        self.assertIn('type', results)
        self.assertEqual('FeatureCollection', results['type'])
        self.assertEqual('kph', results['header']['units'])
        

    def test_point_default_arguments(self):
        """
        Test call to API using default arguments
        """
        results = self.mc.point(self.lats, self.lons)
        self.logger.debug(results)

        self.validate_point_results(results)
        self.assertEqual('FT_GUST', results['header']['terrain_correction'])
        # TODO: fix keyword upstream
        self.assertEqual('3-seconds', results['header']['windspeed_averaing_period'])

    def test_point_ft_gust_3seconds(self):
        results = self.mc.point(self.lats, self.lons, 'Present_Day', 'FT_GUST', '3-seconds')
        self.logger.debug(results)

        self.validate_point_results(results)
        self.assertEqual('FT_GUST', results['header']['terrain_correction'])
        # TODO: fix keyword upstream
        self.assertEqual('3-seconds', results['header']['windspeed_averaing_period'])

    def test_point_ow_gust_1minute(self):
        results = self.mc.point(self.lats, self.lons, 'Present_Day', 'OW', '1-minute')
        self.logger.debug(results)
        self.validate_point_results(results)

        self.assertEqual('OW', results['header']['terrain_correction'])
        # TODO: fix keyword upstream
        self.assertEqual('1-minute', results['header']['windspeed_averaing_period'])

    
    def test_point_ot_gust_1minute(self):
        results = self.mc.point(self.lats, self.lons, 'Present_Day', 'OT', '1-minute')
        self.logger.debug(results)
        self.validate_point_results(results)

        self.assertEqual('OT', results['header']['terrain_correction'])
        # TODO: fix keyword upstream
        self.assertEqual('1-minute', results['header']['windspeed_averaing_period'])


if __name__ == '__main__':
    unittest.main()