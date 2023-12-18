
import sys
import argparse
import pandas as pd
import numpy as np
from math import ceil
from shapely import Polygon
from pathlib import Path
import geopandas as gpd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc
from reaskapi.metryc import Metryc

LAT_NAMES = ['latitude', 'Latitude', 'lat', 'Lat']
LON_NAMES = ['longitude', 'Longitude', 'lon', 'Lon']


def get_hazard(all_lats, all_lons, terrain_correction,
               wind_speed_averaging_period, product='deepcyc', scenario='current_climate',
               time_horizon='now', return_period=None):

    num_calls = ceil(len(all_lats) / 100)
    if return_period is None and product.lower() == 'deepcyc':
        # We are pulling the full stochastic history - do one lat, lon pair at a time.
        num_calls = len(all_lats)

    if product.lower() == 'deepcyc':
        m = DeepCyc()
    else:
        m = Metryc()

    df = None
    for lats, lons in zip(np.array_split(all_lats, num_calls),
                          np.array_split(all_lons, num_calls)):

        if m.product == 'Metryc':
            ret = m.tcwind_events(lats, lons,
                          terrain_correction=terrain_correction,
                          wind_speed_averaging_period=wind_speed_averaging_period)
        elif return_period is not None:
            assert m.product == 'DeepCyc'
            ret = m.tcwind_returnvalues(lats, lons, return_period,
                                        scenario=scenario,
                                        time_horizon=time_horizon,
                                        terrain_correction=terrain_correction,
                                        wind_speed_averaging_period=wind_speed_averaging_period)
        else:
            assert m.product == 'DeepCyc'
            ret = m.tcwind_events(lats, lons, scenario=scenario,
                                    time_horizon=time_horizon,
                                    terrain_correction=terrain_correction,
                                    wind_speed_averaging_period=wind_speed_averaging_period)
            if ret:
                assert ret['header']['scenario'] == scenario
                assert ret['header']['time_horizon'] == time_horizon

        if not ret:
            return None

        assert product in ret['header']['product']
        assert ret['header']['terrain_correction'] == terrain_correction
        assert ret['header']['wind_speed_averaging_period'] == wind_speed_averaging_period

        if df is None:
            df = gpd.GeoDataFrame.from_features(ret)
        else:
            tmp_df = gpd.GeoDataFrame.from_features(ret)
            df = pd.concat((df, tmp_df), ignore_index=True)

    if m.product == 'DeepCyc':
        df['scenario'] = scenario
        df['time_horizon'] = time_horizon
        df['simulation_years'] = ret['header']['simulation_years']

    df['terrain_correction'] = terrain_correction
    df['wind_speed_averaging_period'] = wind_speed_averaging_period
    df['lat'] = df.geometry.centroid.y
    df['lon'] = df.geometry.centroid.x
    df.drop(['geometry'], axis=1, inplace=True)


    return df


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--output_filename', required=True,
                        help="Name of the output CSV file.")
    parser.add_argument('--product', required=False, default='DeepCyc',
                        help="Name of the product to query. DeepCyc or Metryc.")
    parser.add_argument('--location_csv', required=False, default=None,
                        help="CSV file with l(L)atitude l(L)ongitude columns")
    parser.add_argument('--latitudes', required=False, nargs='+', type=float,
                        default=[], help="A list of latitudes")
    parser.add_argument('--longitudes', required=False, nargs='+', type=float,
                        default=[], help="A list of longitudes")
    parser.add_argument('--return_period', required=False, default=None, type=int,
                        help='Get a wind speed for this return period.')
    parser.add_argument('--scenario', required=False, default='current_climate', type=str,
                        help='The climate scenario to use. Can be: current_climate, SSP1-2.6, SSP2-4.5, SSP5-8.5')
    parser.add_argument('--time_horizon', required=False, default='now', type=str,
                        help='The time horizon to use. Can be: now, 2035, 2050, 2065, 2080.')
    parser.add_argument('--terrain_correction', required=False,
                        default='full_terrain_gust',
                        help="Terrain correction should be 'full_terrain_gust', 'open_water', 'open_terrain', 'all_open_terrain'")
    parser.add_argument('--wind_speed_averaging_period', required=False,
                         default='3_seconds')

    args = parser.parse_args()

    assert args.scenario in ['current_climate', 'SSP1-2.6', 'SSP2-4.5', 'SSP5-8.5']
    assert args.time_horizon in ['now', '2035', '2050', '2065', '2080']

    if Path(args.output_filename).exists():
        print(f'Error: output file {args.output_filename} already exists.', file=sys.stderr)
        return 1

    if not args.location_csv:
        if args.latitudes == []:
            print('Error: please use one of  --location_csv or --latitudes, --longitudes')
            parser.print_help()
            return 1

        assert len(args.latitudes) == len(args.longitudes)

        lats = args.latitudes
        lons = args.longitudes
    else:
        input_df = pd.read_csv(args.location_csv)
        lat_col_name = None
        lon_col_name = None
        for tmp_lat, tmp_lon in zip(LAT_NAMES, LON_NAMES):
            if tmp_lat in input_df.columns:
                lat_col_name = tmp_lat
            if tmp_lon in input_df.columns:
                lon_col_name = tmp_lon
        assert lat_col_name is not None
        assert lon_col_name is not None

        lats = list(input_df[lat_col_name])
        lons = list(input_df[lon_col_name])

    df = get_hazard(lats, lons,
                    args.terrain_correction,
                    args.wind_speed_averaging_period,
                    scenario=args.scenario, time_horizon=args.time_horizon,
                    product=args.product, return_period=args.return_period)

    if df is not None:
        df.to_csv(args.output_filename, index_label='index')
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
