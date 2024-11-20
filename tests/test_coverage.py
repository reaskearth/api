import sys
import geopandas as gpd
import pytest
import numpy as np
from all_tile_ids import all_tile_ids, new_zealand_tile_ids, south_pacific_tile_ids
from all_tile_ids import indonesia_tile_ids, north_pacific_tile_ids
from all_tile_ids import australia_tile_ids, south_africa_tile_ids
from all_tile_ids import west_asia_tile_ids

from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

RKG_RES = 2**-7 + 2**-9

# These tiles have no or very low risk so we don't expect a return value
# The present day simulations will have more events here due to the
# longer simulation period
empty_tile_ids = [8459, 8460, 8461, 4763, 4907, 4908, 7589, 7590, 7591, 7732, 7733, 7734, 7735,
    7736, 5052, 7876, 7877, 7881, 2514, 8026, 3175, 8171, 3320, 8315, 8316, 8317]

# These tiles are missing in the climate scenarios for West Asia region
missing_future_climate_west_asia_tile_ids = [6784, 6785, 5773, 6928, 6929, 6930,
    6931, 6932, 6933, 6934, 6935, 6936, 6937, 6206, 5198, 5199, 5200, 5201, 5202,
    6350, 6351, 6352, 6353, 6493, 6494, 5343, 6495, 6496, 6497, 6638, 6639, 6640,
    6641, 6783]

# These tiles are missing in the climate scenarios for The Americas region for 2035 and 2050
missing_near_future_climate_the_americas_tile_ids = [5730, 5731, 5732, 5733, 5734,
5871, 5872, 5873, 5874, 5875, 5876, 5877, 5878, 6015, 6019, 6020, 6024, 6159,
6302, 6442, 6585, 6586, 6587, 6589, 6730, 6731, 6732, 6733, 6880, 7024]

# These tiles are missing in the climate scenarios for The Americas region for 2065 and 2080
missing_far_future_climate_the_americas_tile_ids = [8607, 8608, 8609, 8610,
    8611, 8612, 8613, 8614, 8615]

class TestDeepcycCoverage:
    """
    Test API data coverage
    """

    dc = DeepCyc()
    dc_v208 = DeepCyc(product_version='DeepCyc-2.0.8')

    tile_lons = np.array_split(np.arange(0 + RKG_RES / 2, 360, RKG_RES), 144)
    tile_lats = np.array_split(np.arange(-90 + RKG_RES / 2, 90, RKG_RES), 72)

    def get_tile_status(self, tile_id, scenario, time_horizon):

        tlons = self.tile_lons[tile_id % 144]
        tlats = self.tile_lats[int(tile_id / 144)]

        status = None
        for lat in [tlats.min(), tlats.max()]:
            for lon in [tlons.min(), tlons.max()]:
                ret = self.dc.tcwind_returnvalues(lat, lon, [24000],
                                                    scenario=scenario,
                                                    time_horizon=time_horizon)
                assert ret['header']['time_horizon'] == time_horizon
                assert ret['header']['scenario'] == scenario

                df = gpd.GeoDataFrame.from_features(ret)
                status = df.iloc[0].status
                if status == 'OK':
                    break

            if status == 'OK':
                break

        return status

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

    @pytest.mark.parametrize("scenario", [
        'current_climate', 'SSP1-2.6', 'SSP2-4.5', 'SSP5-8.5'
    ])
    @pytest.mark.parametrize("time_horizon", [
        '2080', 'now', '2035', '2050', '2065',
    ])
    def test_tcwind_tiles_exist(self, scenario, time_horizon):

        if scenario == 'current_climate':
            if time_horizon != 'now':
                return
        else:
            if time_horizon == 'now':
                return

        for tile_id in all_tile_ids:

            status = self.get_tile_status(tile_id, scenario, time_horizon)

            if tile_id in empty_tile_ids:
                # Don't check status here - results will change depending on
                # scenario and time horizon
                continue

            if scenario != 'current_climate':
                # FIXME: no climate scenarios for New Zealand, South Pacific, Indonesia
                if tile_id in new_zealand_tile_ids:
                    assert status == 'NO CONTENT'
                    continue
                if tile_id in south_pacific_tile_ids:
                    assert status == 'NO CONTENT'
                    continue
                if tile_id in indonesia_tile_ids:
                    assert status == 'NO CONTENT'
                    continue

                if tile_id in missing_future_climate_west_asia_tile_ids:
                    assert status == 'NO CONTENT'
                    continue

            if time_horizon in ['2035', '2050']:
                # FIXME: missing tiles in climate scenarios for The Americas, West Asia
                if tile_id in missing_near_future_climate_the_americas_tile_ids:
                    assert status == 'NO CONTENT'
                    continue

            if time_horizon in ['2065', '2080']:
                if tile_id in missing_far_future_climate_the_americas_tile_ids:
                    assert status == 'NO CONTENT'
                    continue

                # FIXME: no 2065, 2080 time horizon for North Pacific
                if tile_id in north_pacific_tile_ids:
                    assert status == 'NO CONTENT'
                    continue

            if time_horizon == '2080':
                # FIXME: no 2080 time horizon for Australia and South Africa
                if tile_id in australia_tile_ids:
                    assert status == 'NO CONTENT'
                    continue
                if tile_id in south_africa_tile_ids:
                    assert status == 'NO CONTENT'
                    continue

            assert status == 'OK'
