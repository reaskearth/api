
import sys
from pathlib import Path
import json
import time

sys.path.append(str(Path(__file__).resolve().parent.parent))
from reaskapi.metryc import Metryc

def main():

    lats = [29.95747]
    lons = [-90.06295]
    mc = Metryc()

    ret = mc.tcwind_events(lats, lons)
    with open('Jackson_Square_Metryc_Present_Day_API_Sample.json', 'w') as f:
        print(json.dumps(ret, indent=4), file=f)


if __name__ == '__main__':
    sys.exit(main())
