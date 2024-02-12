
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
LOCATION_NAMES = ['location', 'Location', 'locationName']
RKG_RES = 2**-7 + 2**-9

def convert_open_water_1minute_to_10minute(df):
    """
    Convert open water wind speed averaging period from 1 minute to 10 minutes using
    WMO Guidlines. See p4 of:
    https://library.wmo.int/records/item/48652-guidelines-for-converting-between-various-wind-averaging-periods-in-tropical-cyclone-conditions
    """

    assert all(df['wind_speed_averaging_period'] == '1_minute'), \
        'Can only convert to 10 minute wind speed averaging from 1 minute'
    assert all(df['terrain_correction'] == 'open_water'), \
        'Can only convert to 10 minutes wind speed averaging over water'

    df['wind_speed'] = df['wind_speed'] * 0.9
    df['wind_speed_averaging_period'] = '10_minutes'

    return df


def _get_hazard(all_lats, all_lons, location_names=None,
                terrain_correction='full_terrain_gust',
                wind_speed_averaging_period='3_seconds',
                product='deepcyc', scenario='current_climate',
                time_horizon='now', return_period=None):

    assert len(all_lats) == len(all_lons), 'Mismatching number of lats and lons'
    if location_names is not None:
        assert len(all_lats) == len(location_names)

    num_calls = ceil(len(all_lats) / 100)
    if return_period is None and product.lower() == 'deepcyc':
        # We are pulling the full stochastic history - do one lat, lon pair at a time.
        num_calls = len(all_lats)

    if product.lower() == 'deepcyc':
        m = DeepCyc()
    else:
        m = Metryc()

    convert_to_10_minute = False
    if wind_speed_averaging_period == '10_minutes':
        convert_to_10_minute = True
        wind_speed_averaging_period = '1_minute'
        assert terrain_correction == 'open_water', \
            '10 minutes wind speed averaging period only supported for Open Water terrain type.'

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

    # Do a spatial join to attach the query locations and location names
    tmp = {'lat': all_lats, 'lon': all_lons}
    if location_names is not None:
        tmp['location_name'] = location_names

    df_locs = gpd.GeoDataFrame(tmp, geometry=gpd.points_from_xy(all_lons, all_lats), crs="EPSG:4326")
    df = df.set_crs(4326).sjoin(df_locs, predicate="contains")
    df.drop(['index_right'], axis=1, inplace=True)

    # Fix up some additional columns
    if m.product == 'DeepCyc':
        df['scenario'] = ret['header']['scenario']
        df['time_horizon'] = ret['header']['time_horizon']
        df['simulation_years'] = ret['header']['simulation_years']

    df['wind_speed_averaging_period'] = ret['header']['wind_speed_averaging_period']
    df['terrain_correction'] = ret['header']['terrain_correction']

    if convert_to_10_minute:
        df = convert_open_water_1minute_to_10minute(df)

    return df

def get_hazard_with_resolution(all_lats, all_lons, location_names=None,
                              terrain_correction='full_terrain_gust',
                              wind_speed_averaging_period='3_seconds',
                              product='deepcyc', scenario='current_climate',
                              time_horizon='now', return_period=None, res=1):
    """
    Get hazard with a particular resolution. The resolution units are Reask grid
    cells which have sides of length (2**-7 + 2**-9) degrees.

    For example a resolution of 3 will be a box have side lengths:

    3*(2**-7 + 2**-9) degress ~= 3.2km x 3.2 km at the equator.
    """

    assert (res % 2) == 1, "Only odd-numbered resolutions are supported."

    # Centre point data frame
    df_cen = _get_hazard(all_lats, all_lons,
                         location_names,
                         terrain_correction=terrain_correction,
                         wind_speed_averaging_period=wind_speed_averaging_period,
                         scenario=scenario, time_horizon=time_horizon,
                         product=product, return_period=return_period)

    if res > 1:
        # Offset lats, lons to lower left corner of target resolution
        ll_lats = all_lats - (np.floor(res / 2)*RKG_RES)
        ll_lons = all_lons - (np.floor(res / 2)*RKG_RES)

        dfs = []
        dfs_ws = []
        for j in range(res):
            for i in range(res):
                tmp_lats = ll_lats + j*RKG_RES
                tmp_lons = ll_lons + i*RKG_RES
                df = _get_hazard(tmp_lats, tmp_lons, location_names,
                                 terrain_correction=terrain_correction,
                                 wind_speed_averaging_period=wind_speed_averaging_period,
                                 scenario=scenario, time_horizon=time_horizon,
                                 product=product, return_period=return_period)
                dfs.append(df)
                dfs_ws.append(df[['location_name', 'wind_speed']])

        # FIXME: do some checks to make sure the geometry corners are as expected
        df = pd.concat(dfs)

        # Get mean of wind speed across locations and replace center cell wind speed
        df_ws = pd.concat(dfs_ws).groupby('location_name').mean().rename(columns={'wind_speed': 'mean_wind_speed'})
        df_cen = df_cen.join(df_ws, on='location_name')

        df_cen.drop(['wind_speed'], axis=1, inplace=True)
        df_cen.rename(columns={'mean_wind_speed': 'wind_speed', 'cell_id': 'center_cell_id'}, inplace=True)

    # Add/remove some columns
    df_cen['resolution_deg'] = RKG_RES*res
    df_cen.drop(['geometry'], axis=1, inplace=True)
    df_cen.sort_values('location_name', inplace=True)

    return df_cen


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
    parser.add_argument('--grid_cell_resolution', required=False, default=1, type=int,
                         help="The resolution of returned values in units of (2**-7 + 2**-9) degrees")

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

        location_col_name = None
        for tmp_name in LOCATION_NAMES:
            if tmp_name in input_df.columns:
                location_col_name = tmp_name

        location_names = None
        if location_col_name is not None:
            location_names = list(input_df[location_col_name])

    df = get_hazard_with_resolution(lats, lons,
                                    location_names,
                                    args.terrain_correction,
                                    args.wind_speed_averaging_period,
                                    scenario=args.scenario, time_horizon=args.time_horizon,
                                    product=args.product, return_period=args.return_period,
                                    res=args.grid_cell_resolution)

    if df is not None:
        df.to_csv(args.output_filename, index_label='index')
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
