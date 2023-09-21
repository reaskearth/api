
import sys
import pytest
from pathlib import Path
import geopandas as gpd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.metryc import Metryc

TEST_LOCATIONS = [(-17.68298, 177.2756)]
TEST_LOCATIONS_MISSING = [(51.0, 11.0)]  # Germany

def call_all_endpoints_at_location(obj, lat, lon, **kwargs):

    rets = []

    r = obj.tctrack_events(lat, lon, 'circle', radius_km=5, **kwargs)
    rets.append(r)
    r = obj.tcwind_events(lat, lon, **kwargs)
    rets.append(r)

    if 'deepcyc' in obj.product.lower():
        r = obj.tcwind_riskscores(lat, lon, **kwargs)
        rets.append(r)
        r = obj.tcwind_returnperiods(lat, lon, 100, **kwargs)
        rets.append(r)
        r = obj.tcwind_returnvalues(lat, lon, 100, **kwargs)
        rets.append(r)
        r = obj.tctrack_returnperiods(lat, lon, 100, 'circle', radius_km=5, **kwargs)
        rets.append(r)
        r = obj.tctrack_returnvalues(lat, lon, 100, 'circle', radius_km=5, **kwargs)
        rets.append(r)

    return rets


class TestHeader:
    """
    Test return header including error messages
    """

    mc = Metryc()
    dc = DeepCyc()

    @pytest.mark.parametrize("lat,lon", TEST_LOCATIONS)
    @pytest.mark.parametrize("prod", [mc, dc])
    def test_tag(self, prod, lat, lon):
        """
        Check that the tag is returned with all endpoints
        """

        tag = 'Hello World!'
        rets = call_all_endpoints_at_location(prod, lat, lon, **{'tag': tag})

        if 'deepcyc' in prod.product.lower():
            assert len(rets) == 7
        else:
            assert len(rets) == 2

        for r in rets:
            if r['header']['tag'] != tag:
                import pdb
                pdb.set_trace()
            assert r['header']['tag'] == tag


    @pytest.mark.parametrize("lat,lon", TEST_LOCATIONS_MISSING)
    @pytest.mark.parametrize("prod", [mc, dc])
    def test_missing_location_message(self, prod, lat, lon):

        ret = prod.tcwind_events(lat, lon)
        df = gpd.GeoDataFrame.from_features(ret)

        assert len(df) == 0

        # FIXME: there should be no message if there is no risk