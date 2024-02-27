
import sys
import time
import argparse
import pandas as pd
import numpy as np
from math import ceil
from shapely import Polygon, union_all
from pathlib import Path
import geopandas as gpd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.deepcyc import DeepCyc
from reaskapi.metryc import Metryc

LAT_NAMES = ['latitude', 'Latitude', 'lat', 'Lat', 'latitude_nr']
LON_NAMES = ['longitude', 'Longitude', 'lon', 'Lon', 'longitude_nr']
LOCATION_IDS = ['unique_id', 'location_id', 'location', 'Location', 'locationName']
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

    df['wind_speed'] = df['wind_speed'] * (1 / 1.05)
    df['wind_speed_averaging_period'] = '10_minutes'

    return df



def _do_queries_serially(all_lats, all_lons,
                         terrain_correction,
                         wind_speed_averaging_period,
                         product, scenario,
                         time_horizon, return_period):

    if product.lower() == 'deepcyc':
        m = DeepCyc()
    else:
        m = Metryc()

    num_calls = ceil(len(all_lats) / 100)
    if return_period is None and product.lower() == 'deepcyc':
        # We are pulling the full stochastic history - do one lat, lon pair at a time.
        num_calls = len(all_lats)

    start_time = time.time()
    all_query_dfs = []
    for lats, lons in zip(np.array_split(all_lats, num_calls),
                          np.array_split(all_lons, num_calls)):

        if (time.time() - start_time) > 3600:
            if product.lower() == 'deepcyc':
                m = DeepCyc()
            else:
                m = Metryc()

            start_time = time.time()
            token_age = 0

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

        assert product in ret['header']['product']
        assert ret['header']['terrain_correction'] == terrain_correction
        assert ret['header']['wind_speed_averaging_period'] == wind_speed_averaging_period

        df = gpd.GeoDataFrame.from_features(ret)
        df['wind_speed_averaging_period'] = ret['header']['wind_speed_averaging_period']
        df['terrain_correction'] = ret['header']['terrain_correction']

        # Fix up some additional columns
        if product.lower() == 'DeepCyc':
            df['scenario'] = ret['header']['scenario']
            df['time_horizon'] = ret['header']['time_horizon']
            df['simulation_years'] = ret['header']['simulation_years']

        df.rename(columns={'wind_speed': 'wind_speed_{}'.format(ret['header']['wind_speed_units'])}, inplace=True)
        all_query_dfs.append(df)

    df = pd.concat(all_query_dfs, ignore_index=True)

    return df


def _do_queries(all_lats, all_lons,
                 terrain_correction,
                 wind_speed_averaging_period,
                 product, scenario,
                 time_horizon, return_period):

    import multiprocessing as mp
    from itertools import repeat

    num_calls = ceil(len(all_lats) / 1000)
    lats = np.array_split(all_lats, num_calls)
    lons = np.array_split(all_lons, num_calls)

    do_parallel = True
    if do_parallel:
        num_procs = 8
    else:
        num_procs = 1

    with mp.Pool(num_procs) as pool:
        dfs = pool.starmap(_do_queries_serially,
                            zip(lats, lons,
                               repeat(terrain_correction),
                               repeat(wind_speed_averaging_period),
                               repeat(product),
                               repeat(scenario),
                               repeat(time_horizon),
                               repeat(return_period)))

    df = pd.concat(dfs, ignore_index=True)
    return df


def _get_hazard(all_lats, all_lons, location_ids=None,
                terrain_correction='full_terrain_gust',
                wind_speed_averaging_period='3_seconds',
                product='deepcyc', scenario='current_climate',
                time_horizon='now', return_period=None):

    assert len(all_lats) == len(all_lons), 'Mismatching number of lats and lons'
    if location_ids is not None:
        assert len(all_lats) == len(location_ids)

    convert_to_10_minute = False
    if wind_speed_averaging_period == '10_minutes':
        convert_to_10_minute = True
        wind_speed_averaging_period = '1_minute'
        assert terrain_correction == 'open_water', \
            '10 minutes wind speed averaging period only supported for Open Water terrain type.'

    df = _do_queries(all_lats, all_lons, terrain_correction,
                     wind_speed_averaging_period,
                     product, scenario,
                     time_horizon, return_period)

    # FIXME: API-112 we may get duplicates if there is more than one query
    # within the same grid cell.
    df = df.drop_duplicates()

    # Do a spatial join to attach the query locations and location names
    tmp_df = pd.DataFrame({'lat': all_lats, 'lon': all_lons})
    if location_ids is not None:
        tmp_df[location_ids.name] = list(location_ids)
        tmp_df.set_index(location_ids.name)

    df_locs = gpd.GeoDataFrame(tmp_df, geometry=gpd.points_from_xy(all_lons, all_lats), crs="EPSG:4326")
    df = df.set_crs(4326).sjoin(df_locs, predicate="intersects")
    df.drop(['index_right'], axis=1, inplace=True)

    if convert_to_10_minute:
        df = convert_open_water_1minute_to_10minute(df)

    if location_ids is not None:
        assert set(df[location_ids.name]) == set(location_ids)

    return df


def get_hazard_with_resolution_or_halo(all_lats, all_lons, location_ids=None,
                              terrain_correction='full_terrain_gust',
                              wind_speed_averaging_period='3_seconds',
                              product='deepcyc', scenario='current_climate',
                              time_horizon='now', return_period=None, regrid_res=1,
                              regrid_op='mean', halo_size=0):
    """
    Get hazard with a particular resolution or with a halo.

    The resolution units are Reask grid cells which have sides of length (2**-7
    + 2**-9) degrees. For example a resolution of 3 will be a box have side
    lengths:

    3*(2**-7 + 2**-9) degress ~= 3.2km x 3.2 km at the equator.

    The halo units are number of grid cells surrounding the point of interest.
    For example a halo of 1 will add a 1 grid cell layer around the centre
    point resulting in 9 new cells being returned. A halo of 2 would be
    (2*2 + 1)^2 = 25 cells
    """

    assert (regrid_res % 2) == 1, "Only odd-numbered resolutions are supported."

    # Centre point data frame
    df_cen = _get_hazard(all_lats, all_lons,
                         location_ids,
                         terrain_correction=terrain_correction,
                         wind_speed_averaging_period=wind_speed_averaging_period,
                         scenario=scenario, time_horizon=time_horizon,
                         product=product, return_period=return_period)

    if regrid_res > 1 or halo_size > 0:
        # Offset lats, lons to lower left corner
        if halo_size > 0:
            side_len = halo_size*2 + 1
        else:
            side_len = regrid_res

        ll_lats = all_lats - (np.floor(side_len / 2)*RKG_RES)
        ll_lons = all_lons - (np.floor(side_len / 2)*RKG_RES)

        dfs = []
        dfs_ws = []
        for j in range(side_len):
            for i in range(side_len):
                tmp_lats = ll_lats + j*RKG_RES
                tmp_lons = ll_lons + i*RKG_RES
                df = _get_hazard(tmp_lats, tmp_lons, location_ids,
                                 terrain_correction=terrain_correction,
                                 wind_speed_averaging_period=wind_speed_averaging_period,
                                 scenario=scenario, time_horizon=time_horizon,
                                 product=product, return_period=return_period)
                dfs.append(df)
                dfs_ws.append(df[['location_id', 'wind_speed_kph']])

        # Checks that we got neighbouring cells that fit inside a square
        test_polys = [dfs[i].sort_values('cell_id').iloc[0].geometry for i in range(len(dfs))]
        test_cell = union_all(test_polys)
        assert test_cell.area == (RKG_RES*side_len)**2, "Error in regridding, wrong area."
        min_lon, min_lat, max_lon, max_lat = test_cell.bounds
        assert max_lat - min_lat == side_len*RKG_RES, "Error in regridding, wrong dlat."
        assert max_lon - min_lon == side_len*RKG_RES, "Error in regridding, wrong dlon."

        if halo_size > 0:
            df_cen = pd.concat(dfs)
            assert len(df_cen) == len(all_lats)*side_len**2

        else:
            assert regrid_res > 1

            # Get mean of wind speed across locations and replace center cell wind speed
            if regrid_op == 'mean':
                df_ws = pd.concat(dfs_ws).groupby('location_id').mean()
            elif regird_op == 'median':
                df_ws = pd.concat(dfs_ws).groupby('location_id').median()
            else:
                assert regrid_op == 'max'
                df_ws = pd.concat(dfs_ws).groupby('location_id').max()

            df_ws.rename(columns={'wind_speed_kph': 'regridded_wind_speed'}, inplace=True)

            df_cen = df_cen.join(df_ws, on='location_id')

            df_cen.drop(['wind_speed_kph'], axis=1, inplace=True)
            df_cen.rename(columns={'regridded_wind_speed': 'wind_speed_kph', 'cell_id': 'center_cell_id'}, inplace=True)


    # Add/remove some columns
    if regrid_res > 1:
        df_cen['resolution_deg'] = RKG_RES*regrid_res
    df_cen.drop(['geometry'], axis=1, inplace=True)

    # FIXME: see API-108: API can return "best effort" return period for
    # location with very low risk.
    if return_period is not None:
        df_cen.loc[df_cen.return_period != return_period, 'wind_speed_kph'] = np.nan
        df_cen.loc[df_cen.return_period != return_period, 'status'] = 'NO CONTENT'
        df_cen.loc[df_cen.return_period != return_period, 'return_period'] = return_period

    return df_cen


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--output_filename', required=False, default=None,
                        help="Name of the output CSV file, otherwise output to stdout")
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
    parser.add_argument('--regrid_resolution', required=False, default=1, type=int,
                         help="The regridding resolution in units of (2**-7 + 2**-9) degrees. Must be an odd number.")
    parser.add_argument('--regrid_operation', required=False, default='mean', type=str,
                         help="The of operation used to regrid to a new resolution. Supports: 'mean', 'median' or 'max'")
    parser.add_argument('--halo_size', required=False, default=0, type=int,
                         help="Put a halo of <size> grid cells around the requested locations.")
    parser.add_argument('--noheader', required=False, action='store_true', default=False,
                         help="Don't add CSV header line to output")


    args = parser.parse_args()

    assert args.scenario in ['current_climate', 'SSP1-2.6', 'SSP2-4.5', 'SSP5-8.5']
    assert args.time_horizon in ['now', '2035', '2050', '2065', '2080']

    if args.product.lower() == 'metryc':
        assert args.regrid_resolution == 1, 'Regrid not supported for Metryc'
        assert args.halo_size == 0, 'Halo not supported for Metryc'

    assert (args.regrid_resolution >= 1) and (args.regrid_resolution % 2 == 1), \
        'Regrid resolution must be odd and >= 1'

    if args.halo_size > 0:
        assert args.regrid_resolution == 1, "Halo and regrid options can't be used together"

    if args.output_filename is not None and Path(args.output_filename).exists():
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

        # FIXME: API-109 better handling on NaN values at server-side
        input_df = input_df[input_df[lat_col_name].notna() & input_df[lon_col_name].notna()]

        lats = list(input_df[lat_col_name])
        lons = list(input_df[lon_col_name])

        location_id_col = None
        for tmp_name in LOCATION_IDS:
            if tmp_name in input_df.columns:
                location_id_col= tmp_name

        location_ids = None
        if location_id_col is not None:
            location_ids = input_df[location_id_col]
            assert len(location_ids) == len(location_ids.unique()), \
                'Location ids are not unique'

    df = get_hazard_with_resolution_or_halo(lats, lons,
            location_ids, args.terrain_correction, args.wind_speed_averaging_period,
            scenario=args.scenario, time_horizon=args.time_horizon,
            product=args.product, return_period=args.return_period,
            regrid_res=args.regrid_resolution,
            regrid_op=args.regrid_operation,
            halo_size=args.halo_size)

    if df is not None:
        if args.output_filename is not None:
            # Output to file
            df.to_csv(args.output_filename, index=False, index_label='index', header=not args.noheader)
        else:
            # Output to stdout
            df.to_csv(sys.stdout, index=False, index_label='index', header=not args.noheader)
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
