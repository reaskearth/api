

import sys
import pytest
from pathlib import Path    
import geopandas as gpd
import numpy as np

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.metryc import Metryc

import requests

def call_v1_metryc_point(access_token, lats, lons):
    url = 'https://api.reask.earth/v1/metryc/point'
    params = {
        'access_token': access_token,
        'peril': 'TC_Wind',
        'lats': lats,
        'lons': lons
    }

    res = requests.get(url, params=params)
    assert res.status_code == 200, 'API GET request failed'

    return res.json()

def call_v1_deepcyc_pointaep(access_token, lats, lons, return_period):

    aeps = list(1 / np.array(return_period))

    url = 'https://api.reask.earth/v1/deepcyc/pointaep'
    params = {
        'access_token': access_token,
        'peril': 'TC_Wind',
        'lats': lats,
        'lons': lons,
        'aeps': aeps
    }

    res = requests.get(url, params=params)
    assert res.status_code == 200, 'API GET request failed'
    return res.json()


class TestCompareV1andV2:
    """
    Compare output from v1 and v2 of the API
    """

    mc = Metryc()
    dc = DeepCyc()


    @pytest.mark.parametrize("lats,lons", [
        ([29.95747], [-90.06295])
    ])
    def test_metryc_storms(self, lats, lons):
        ret_v2 = self.mc.tcwind_events(lats, lons)
        df_v2 = gpd.GeoDataFrame.from_features(ret_v2)

        ret_v1 = call_v1_metryc_point(self.mc.access_token, lats, lons)
        df_v1 = gpd.GeoDataFrame.from_features(ret_v1)

        assert ret_v2['header']['product'] == ret_v1['header']['product']
        assert sorted(df_v1.storm_names.iloc[0]) == sorted(df_v2.name)
        assert sorted(sorted(df_v1.windspeeds.iloc[0])) == sorted(df_v2.wind_speed)


    @pytest.mark.parametrize("lats,lons,return_period", [
        ([29.95747], [-90.06295], [10, 25, 50, 100, 250, 500])
    ])
    def test_deepcyc_returnvalues(self, lats, lons, return_period):

        ret_v2 = self.dc.tcwind_returnvalues(lats, lons, return_period=return_period)
        df_v2 = gpd.GeoDataFrame.from_features(ret_v2)

        ret_v1 = call_v1_deepcyc_pointaep(self.mc.access_token, lats, lons, return_period)
        df_v1 = gpd.GeoDataFrame.from_features(ret_v1)

        assert ret_v2['header']['product'] == ret_v1['header']['product']
        assert list(df_v2.wind_speed) == df_v1.iloc[0].windspeeds