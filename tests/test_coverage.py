
import geopandas as gpd
import sys
import pytest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

class TestCoverage:
    """
    Test API data coverage
    """

    dc = DeepCyc()
    dc_v208 = DeepCyc(product_version='DeepCyc-2.0.8')

    @pytest.mark.parametrize("lat,lon", [
        (8.5, 171), (6, 171), (6, 168.5), (8.5, 168.5),  # Marshall Islands
        (6, 160), # Micronesia
        (7.5, 134.5) # Palau
    ])
    @pytest.mark.parametrize("dc_ver", ['default', 'new'])
    def test_remote_locations(self, dc_ver, lat, lon):
        """
        Check our stochastic track coverage in specific remote locations.

        A useful test to check whether we expect risk in these places.
        """
        if dc_ver == 'default':
            dc = self.dc
            expected_sim_years = 41000
        else:
            assert dc_ver == 'new'
            dc = self.dc_v208
            expected_sim_years = 66000

        ret = dc.tctrack_events(lat, lon, 'circle', radius_km=100)
        df_track = gpd.GeoDataFrame.from_features(ret)

        assert ret['header']['simulation_years'] == expected_sim_years
        assert len(df_track) > 1000

        ret = dc.tcwind_events(lat, lon)
        df_wind = gpd.GeoDataFrame.from_features(ret)

        if len(df_wind) == 1:
            assert df_wind.iloc[0].status == 'NO CONTENT'
            assert '2.0.8' not in ret['header']['product']
        else:
            assert ret['header']['simulation_years'] == expected_sim_years
            assert len(df_wind) > 1000
            assert len(set(df_track.event_id).intersection(df_wind.event_id)) > 0
