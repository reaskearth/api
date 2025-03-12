
import sys
import uuid
import pytest
import numpy as np
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

default_params = { "scenario": "current_climate",
            "time_horizon": "now",
            "terrain_correction": "full_terrain_gust",
            "wind_speed_averaging_period": "3_seconds",
            "wind_speed_units": "kph" }


class TestPayout():
    dc = DeepCyc()

    def make_payout_request(self, lats, lons, location_event_limits,
                             portfolio_event_limit, portfolio_annual_limit):

        my_dir = Path(__file__).parent.resolve()

        df_payout = pd.read_csv(my_dir / 'example_payout_table.csv')
        payout_table_id = str(uuid.uuid4())
        payout_tables = [
            {
                "id": payout_table_id,
                "wind_speed": list(df_payout.wind_speed_kph),
                "payout_ratio": list(df_payout.payout_ratio)
            },
        ]

        geoms = []
        location_props = []
        for lat, lon, loc_event_limit in zip(lats, lons, location_event_limits):

            location_props.append({
                "id": '0',
                "location_event_limit": loc_event_limit,
                "payout_table_id": payout_table_id
            })
            geoms.append(Point(lon, lat))

        # Convert to GeoJSON format
        df = gpd.GeoDataFrame(location_props, geometry=[Point(lon, lat)])
        portfolio = json.loads(df.to_json())
        portfolio["properties"] = {
            "name": "My Portfolio",
            "id": '0',
            "portfolio_event_limit": portfolio_event_limit,
            "portfolio_annual_limit": portfolio_annual_limit
        }

        return portfolio, payout_tables

    @pytest.mark.parametrize("lat,lon", [
        (31.0, -85.0),
    ])
    def test_deepcyc_payout(self, lat, lon):

        location_event_limit = 50000
        portfolio_event_limit = 100000
        portfolio_annual_limit = 100000
        portfolio, payout_tables = self.make_payout_request([lat], [lon],
                                         [location_event_limit],
                                           portfolio_event_limit,
                                             portfolio_annual_limit)

        res = self.dc.tcwind_payout(portfolio, payout_tables, **default_params)

        df_event = pd.DataFrame(res['event_payouts'])
        df_annual = pd.DataFrame(res['annual_payouts'])

        # Check limits
        event_limit = min(portfolio_event_limit, location_event_limit)
        assert df_event.payout.max() <= event_limit
        assert df_annual.payout.max() <= portfolio_annual_limit
        assert df_event.groupby('id')['payout'].max().item() <= event_limit

        min_wind_speed = payout_tables[0]['wind_speed'][0]
        assert min_wind_speed == min(payout_tables[0]['wind_speed'])
        assert len(df_event[df_event.wind_speed < min_wind_speed]) == 0

        # Check individual event payouts
        total_payout_for_year = {}
        for _, row in df_event.iterrows():
            payout_ratio_idx = len(payout_tables[0]['payout_ratio']) - 1
            for ws in np.flip(payout_tables[0]['wind_speed']):
                if row.wind_speed >= ws:
                    break
                else:
                    payout_ratio_idx -= 1

            if row.year_id in total_payout_for_year:
                total_payout_for_year[row.year_id] += row.payout
            else:
                total_payout_for_year[row.year_id] = row.payout

            assert row.payout == payout_tables[0]['payout_ratio'][payout_ratio_idx] * event_limit

        # Check annual payouts
        for _, row in df_annual.iterrows():
            assert total_payout_for_year[row.year] == row.payout


    @pytest.mark.parametrize("lat,lon,location_event_limit", [
        (31.0, -85.0, 15000),
    ])
    def test_location_event_limit(self, lat, lon, location_event_limit):
        
        portfolio, payout_table = self.make_payout_request([lat], [lon], [location_event_limit],
                                                           100000, 100000)
        res = self.dc.tcwind_payout(portfolio, payout_table, **default_params)

    @pytest.mark.parametrize("lat,lon,portfolio_event_limit", [
        (31.0, -85.0, 15000),
    ])
    def test_portfolio_event_limit(self, lat, lon, portfolio_event_limit):

        portfolio, payout_table = self.make_payout_request([lat], [lon], [100000],
                                                           portfolio_event_limit, 100000)
        res = self.dc.tcwind_payout(portfolio, payout_table, **default_params)

    @pytest.mark.parametrize("lat,lon,portfolio_annual_limit", [
        (31.0, -85.0, 15000),
    ])
    def test_portfolio_annual_limit(self, lat, lon, portfolio_annual_limit):

        portfolio, payout_table = self.make_payout_request([lat], [lon], [100000],
                                                           100000, 100000)
        res = self.dc.tcwind_payout(portfolio, payout_table, **default_params)