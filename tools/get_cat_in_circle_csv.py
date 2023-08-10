
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


def get_cat_in_circle(center_lat, center_lon, radius_km, terrain_correction,
                      wind_speed_averaging_period, product, return_period=None):

    if product.lower() == 'deepcyc':
        m = DeepCyc()
    else:
        assert product.lower() == 'metryc'
        m = Metryc()

    if m.product == 'DeepCyc' and return_period is not None:
        ret = m.tctrack_returnvalues(center_lat, center_lon, 'circle', radius_km, return_period,
                                     terrain_correction=terrain_correction,
                                     wind_speed_averaging_period=wind_speed_averaging_period)
    else:
        ret = m.tctrack_events(center_lat, center_lon, 'circle', radius_km=radius_km,
                      terrain_correction=terrain_correction,
                      wind_speed_averaging_period=wind_speed_averaging_period)

    df = gpd.GeoDataFrame.from_features(ret)
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
    parser.add_argument('--center_lat', required=True, type=float,
                        help="Latitude of circle center point")
    parser.add_argument('--center_lon', required=True, type=float,
                        default=[], help="Longitude of circle center point")
    parser.add_argument('--radius_km', required=True, type=float,
                        default=[], help="Radius of circle in km")
    parser.add_argument('--return_period', required=False, default=None, type=int,
                        help='Get a wind speed for this return period.')
    parser.add_argument('--terrain_correction', required=False,
                        default='open_water',
                        help="Terrain correction should be 'full_terrain_gust', 'open_water', 'open_terrain', 'all_open_terrain'")
    parser.add_argument('--wind_speed_averaging_period', required=False,
                         default='1_minute')

    args = parser.parse_args()

    df = get_cat_in_circle(args.center_lat, args.center_lon, args.radius_km,
                    args.terrain_correction,
                    args.wind_speed_averaging_period,
                    product=args.product, return_period=args.return_period)

    df.to_csv(args.output_filename, index_label='index')


if __name__ == '__main__':
    sys.exit(main())
