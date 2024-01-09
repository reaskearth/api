
import sys
import argparse
from pathlib import Path
import geopandas as gpd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.metryc import Metryc


def make_output_filename(args):

    import pdb
    pdb.set_trace()

    terrain_map = {'full_terrain_gust': 'FT',
                   'open_water': 'OW',
                   'open_terrain': 'OT'}
    
    if args.storm_name:
        template = '{storm_name}_{storm_season}'
    else:
        template = '{storm_id}'

    suffix = args.format
    if args.format == 'geotiff':
        suffix = 'tiff'

    terrain_correction = terrain_map[args.terrain_correction]
    wind_speed_averaging_period = args.wind_speed_averaging_period

    template += '_{terrain_correction}_{wind_speed_averaging_period}_kph.' + suffix

    output_filename = template.format(*args)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--bbox', required=True, nargs='+', type=float,
                        help="Bounding box in form min_lat max_lat min_lon max_lon.")
    parser.add_argument('--format', required=False, default='geotiff', type=str,
                        help="File format of return value. Gan be geojson or geotiff.")
    parser.add_argument('--storm_name', required=False, default=None, type=str,
                        help='The name of the storm. To be used in conjunction with --storm_year')
    parser.add_argument('--storm_season', required=False, default=None, type=int,
                        help='The season of the storm. To be used in conjunction with --storm_name')
    parser.add_argument('--storm_id', required=False, default=None, type=str,
                        help='The storm id. Alternative to --storm_name and --storm_year')
    parser.add_argument('--terrain_correction', required=False,
                        default='full_terrain_gust',
                        help="Terrain correction should be 'full_terrain_gust', 'open_water', 'open_terrain'")
    parser.add_argument('--wind_speed_averaging_period', required=False, default='3_seconds', 
                        help="Wind speed averaging period should be '3_seconds or 1_minute")

    args = parser.parse_args()

    if args.storm_name and not args.storm_season:
        print('Please provide both storm_name and storm_season')
        parser.print_help()
        return 1

    if not args.storm_name and not args.storm_id:
        print('Please provide storm_name and storm_season or storm_id')
        parser.print_help()
        return 1

    if len(args.bbox) != 4:
        print('Incorrect number coordinates for bounding box.')
        parser.print_help()
        return 1

    min_lat = args.bbox[0]
    max_lat = args.bbox[1]
    min_lon = args.bbox[2]
    max_lon = args.bbox[3]

    if min_lat > max_lat:
        print('Bounding box min_lat larger than max_lat.')
        parser.print_help()
        return 1

    if min_lon > max_lon:
        print('Bounding box min_lon larger than max_lon.')
        parser.print_help()
        return 1

    output_filename = make_output_filename(args)
    if Path(args.output_filename).exists():
        print(f'Error: output file {args.output_filename} already exists.', file=sys.stderr)
        return 1

    m = Metryc()
    ret = m.tcwind_footprint(min_lat, max_lat, min_lon, max_lon,
                             storm_name=args.storm_name,
                             storm_season=args.storm_season,
                             storm_id=args.storm_id,
                             format=args.format,
                             terrain_correction=args.terrain_correction,
                             wind_speed_averaging_period=args.wind_speed_averaging_period)
    import pdb
    pdb.set_trace()


if __name__ == '__main__':
    sys.exit(main())
