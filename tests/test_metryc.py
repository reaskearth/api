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


    @pytest.mark.parametrize("lats,lons,name", [
        ([29.95747], [-90.06295], 'Katrina')
    ])
    def test_tcwind_simple(self, lats, lons, name):
        ret = self.mc.tcwind_events(lats, lons)
        df = gpd.GeoDataFrame.from_features(ret)

        assert name in list(df.name)


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

        assert len(df) > 30

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