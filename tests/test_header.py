
import sys
import pytest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.metryc import Metryc

TEST_LOCATIONS = [(-17.68298, 177.2756)]

def call_all_endpoints_at_location(obj, lat, lon, **kwargs):

    rets = []
    expected_product_names = []

    r = obj.tctrack_events(lat, lon, 'circle', radius_km=5, **kwargs)
    rets.append(r)
    r = obj.tcwind_events(lat, lon, **kwargs)
    rets.append(r)

    if 'metryc' in obj.product.lower():
        expected_product_names = ['Metryc Historical', 'Metryc Historical']
        r = obj.live_tcwind_list(**kwargs)
        rets.append(r)
        expected_product_names.append('Metryc Live')
        r = obj.historical_tcwind_list(**kwargs)
        rets.append(r)
        expected_product_names.append('Metryc Historical')
    else:
        assert 'deepcyc' in obj.product.lower()
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

        expected_product_names = ['DeepCyc Tracks', 'DeepCyc Events', 'DeepCyc Riskscores',
                                  'DeepCyc Maps', 'DeepCyc Maps', 'DeepCyc Tracks', 'DeepCyc Tracks']


    return rets, expected_product_names


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
        rets, _ = call_all_endpoints_at_location(prod, lat, lon, **{'tag': tag})

        if 'deepcyc' in prod.product.lower():
            assert len(rets) == 7
        else:
            assert len(rets) == 4

        for r in rets:
            assert r['header']['tag'] == tag


    @pytest.mark.parametrize("lat,lon", TEST_LOCATIONS)
    @pytest.mark.parametrize("prod", [mc, dc])
    def test_product(self, prod, lat, lon):
        """
        Check that the correct product is returned on all endpoints
        """

        rets, expected_prods = call_all_endpoints_at_location(prod, lat, lon)

        for ret, product_name in zip(rets, expected_prods):
            assert product_name in ret['header']['product']


    @pytest.mark.parametrize("lat,lon", TEST_LOCATIONS)
    @pytest.mark.parametrize("prod", [mc, dc])
    def test_product_versions(self, prod, lat, lon):
        """
        Check that the correct product version is returned on all endpoints
        """

        rets, _ = call_all_endpoints_at_location(prod, lat, lon)

        for ret in rets:
            if 'Metryc' in ret['header']['product']:
                assert 'v1.0.5' in ret['header']['product']
            else:
                assert 'DeepCyc' in ret['header']['product']
                assert 'v2.0.6' in ret['header']['product']
