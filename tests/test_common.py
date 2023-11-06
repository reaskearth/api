import sys
import pytest
from pathlib import Path
import geopandas as gpd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.metryc import Metryc

def df_to_dict(df):

    if 'name' in df:
        keys = [f'{name}_{year}' for name, year in zip(df.name, df.year)]
    else:
        keys = [f'{event_id}' for event_id in df.event_id]

    return dict(zip(keys, df.wind_speed))

class TestCommon:

    mc = Metryc()
    dc = DeepCyc()

    @pytest.mark.parametrize("lats,lons", [
        ([36.8], [-76]), # Virginia Beach
        #([29.95747], [-90.06295]), # Gulf of Mexico
        #([12.0], [125.0]) # Phillipines
    ])
    @pytest.mark.parametrize("prod", [mc, dc])
    def test_tcwind_terrain(self, prod, lats, lons):

        # FIXME: API-50 terrain correction options disabled in Metryc endpoint
        if 'Metryc' in prod.product:
            return

        ret = prod.tcwind_events(lats, lons)
        assert ret['header']['terrain_correction'] == 'full_terrain_gust'
        assert ret['header']['wind_speed_averaging_period'] == '3_seconds'

        ret = prod.tcwind_events(lats, lons, terrain_correction='full_terrain_gust', wind_speed_averaging_period='3_seconds')
        assert ret['header']['terrain_correction'] == 'full_terrain_gust'
        assert ret['header']['wind_speed_averaging_period'] == '3_seconds'

        df1 = gpd.GeoDataFrame.from_features(ret)
        ft_gust = df_to_dict(df1)

        ret = prod.tcwind_events(lats, lons, terrain_correction='open_water')
        assert ret['header']['terrain_correction'] == 'open_water'
        assert ret['header']['wind_speed_averaging_period'] == '3_seconds'
        df2 = gpd.GeoDataFrame.from_features(ret)
        ow_gust = df_to_dict(df2)

        # We expect these to all be greater, becuase open water gust is higher
        # that full terrain gust in this location
        for k in ft_gust:
            assert ow_gust[k] > ft_gust[k]

        ret = prod.tcwind_events(lats, lons, terrain_correction='open_water', wind_speed_averaging_period='1_minute')
        assert ret['header']['terrain_correction'] == 'open_water'
        assert ret['header']['wind_speed_averaging_period'] == '1_minute'
        df3 = gpd.GeoDataFrame.from_features(ret)
        ow_1min = df_to_dict(df3)
        # Gust should always be greater that 1 minute sustained
        for k in ow_gust:
            assert ow_gust[k] > ow_1min[k]

        ret = prod.tcwind_events(lats, lons, terrain_correction='open_terrain')
        assert ret['header']['terrain_correction'] == 'open_terrain'
        assert ret['header']['wind_speed_averaging_period'] == '3_seconds'
        df4 = gpd.GeoDataFrame.from_features(ret)
        ot_gust = df_to_dict(df4)

        # We expect this to be less than the open water
        for k in ow_gust:
            assert ot_gust[k] < ow_gust[k]

        ret = prod.tcwind_events(lats, lons, terrain_correction='open_terrain', wind_speed_averaging_period='1_minute')
        assert ret['header']['terrain_correction'] == 'open_terrain'
        assert ret['header']['wind_speed_averaging_period'] == '1_minute'
        df5 = gpd.GeoDataFrame.from_features(ret)
        ot_1min = df_to_dict(df5)
        # Gust should always be greater that 1 minute sustained
        for k in ot_gust:
            assert ot_gust[k] > ot_1min[k]


    @pytest.mark.parametrize("prod", [mc, dc])
    @pytest.mark.parametrize("lats,lons", [
        ([36.8], [-76]), # Virginia Beach
        #([29.95747], [-90.06295]) # Gulf of Mexico
    ])
    @pytest.mark.parametrize("wind_speed_units", ['kph', 'mph', 'kts', 'ms'])
    def test_units(self, prod, lats, lons, wind_speed_units):

        ret_kph = prod.tcwind_events(lats, lons)
        ws_kph = ret_kph['features'][0]['properties']['wind_speed']
        assert ret_kph['header']['wind_speed_units'] == 'kph'

        ret = prod.tcwind_events(lats, lons, wind_speed_units=wind_speed_units)
        ws_other = ret['features'][0]['properties']['wind_speed']
        assert ret['header']['wind_speed_units'] == wind_speed_units

        if wind_speed_units == 'kph':
            multiplier = 1
        elif wind_speed_units == 'mph':
            multiplier = 1.609344
        elif wind_speed_units == 'kts':
            multiplier = 1.8520000118528
        elif wind_speed_units == 'ms':
            multiplier = 3.6

        assert ws_kph == round(ws_other*multiplier)

        ret_kph = prod.tctrack_events(lats[0], lons[0], 'circle', radius_km=50)
        ws_kph = ret_kph['features'][0]['properties']['wind_speed']
        assert ret_kph['header']['wind_speed_units'] == 'kph'

        ret = prod.tctrack_events(lats[0], lons[0], 'circle', radius_km=50, wind_speed_units=wind_speed_units)
        ws_other = ret['features'][0]['properties']['wind_speed']
        assert ret['header']['wind_speed_units'] == wind_speed_units

        assert ws_kph == round(ws_other*multiplier)
