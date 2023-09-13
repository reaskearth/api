
import geopandas as gpd
import pytest
import sys
import numpy as np

from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc

LOCATIONS_USA = [
    # Miami
    (25.75, -80.24),
    # Virginia Beach
    (36.8, -76),
    # Charleston
    (32.8, -80.0),
    # New Orleans
    (29.966667, -90.080556),
    # Jacksonville
    (30.35, -81.7),
    # Houston
    (29.75, -95.35),
    # New York
    (40.75, -74.0),
    # Philadelphia
    (40, -75.0),
    # Mobile
    (30.7, -88.1),
    # Tampa
    (28.0, -82.5),
]

CLIMATE_SCENARIOS = [
    ('current_climate', 'now'),
    ('SSP1-2.6', '2035'),
    ('SSP2-4.5', '2035'),
    ('SSP5-8.5', '2035'),
    ('SSP1-2.6', '2050'),
    ('SSP2-4.5', '2050'),
    ('SSP5-8.5', '2050'),
]

class TestRiskScores:

    dc = DeepCyc()

    @pytest.mark.parametrize("scenario,time_horizon", CLIMATE_SCENARIOS)
    @pytest.mark.parametrize("lat,lon", LOCATIONS_USA)
    def test_tcwind_climate_risk_scores(self, lat, lon, scenario, time_horizon):

        ret = self.dc.tcwind_riskscores(lat, lon, scenario=scenario, time_horizon=time_horizon)
        df = gpd.GeoDataFrame.from_features(ret)

        assert ret['header']['scenario'] == scenario
        assert ret['header']['time_horizon'] == time_horizon

        assert ret['header']['message'] is None
        assert df.wind_risk_score.iloc[0] < 5 and df.wind_risk_score.iloc[0] > 0.1
        assert len(set(df.cell_id)) == 1

        cat_rs = df.ts_wind_risk_score + df.cat1_wind_risk_score + df.cat2_wind_risk_score + \
                     df.cat3_wind_risk_score + df.cat4_wind_risk_score + df.cat5_wind_risk_score
        assert abs(1 - (cat_rs.item() / df.wind_risk_score.item())) < 1e-6

    def test_normalized_risk_scores(self):

        lats, lons = zip(*LOCATIONS_USA)
        ret = self.dc.tcwind_riskscores(lats, lons)
        df = gpd.GeoDataFrame.from_features(ret).sort_values(by='cell_id')

        scale = 100 / df.wind_risk_score.max()
        present_day_normalized_scores = df.wind_risk_score * scale

        # Now see how a future climate scenario looks compared to these
        ret = self.dc.tcwind_riskscores(lats, lons, scenario='SSP5-8.5', time_horizon='2050')
        df = gpd.GeoDataFrame.from_features(ret).sort_values(by='cell_id')
        future_normalized_scores = df.wind_risk_score * scale

        assert (np.array(future_normalized_scores) > np.array(present_day_normalized_scores)).all()