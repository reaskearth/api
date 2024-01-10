
# Reask API Client

## Introduction

The Reask API currently supports two products:

 * [DeepCyc](https://reask.earth/products/): a high-resolution probabilistic view of tropical cyclone (TC) risk everywhere in the world, both under current as well as future climate scenarios.
 * [Metryc](https://reask.earth/products/): high-resolution tropical cyclone (TC) windspeed estimates for historical events based on our ML windfield model and incorporating agency best track data.

### API Versions

 * [v1](https://github.com/reaskearth/api/tree/v1)
 * [v2](https://github.com/reaskearth/api/tree/main) (this page)


## Package Status

| Branch | Status |
|--------|--------|
| main | [![Build Status](https://github.com/reaskearth/api/actions/workflows/github-actions-ci.yaml/badge.svg)](https://github.com/reaskearth/api/actions/workflows/github-actions-ci.yaml) |


## OpenAPI Documentation and Examples

The interactive documentation can be found here: https://api.reask.earth/v2/docs. You will need to authenticate using you Reask credentials by clicking on the **lock** icon.

Example code for all endpoints can be found in the `tests` directory.

## Quickstart and Tools

Put your Reask credentials into a file called `.reask` in your HOME directory using the following format:

```
[default]
username = <USERNAME_OR_EMAIL>
password = <PASSWORD>
```

Check the permissions of this file and make sure it is only readable by yourself by running the following command:

```
chmod 600 ~/.reask
```

Then visit https://github.com/reaskearth/api/ to access the Python3 API client code.  It can be downloaded by either clicking on the green **Code** button or using the `git` command as follows:

```
git clone https://github.com/reaskearth/api.git reaskapi
```

Once downloaded you can test the code by running one of the tools in the `tools` folder. For example the `get_hazard_csv.py` script uses DeepCyc and Metryc to give global TC risk across many climate scenarios and time horizons including the present day:
```Bash
# Change the current directory to the tools folder
cd reaskapi
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
cd tools

# Create a locations.csv file with the points of interest.
# This will create a locations file with three spoints
echo "lat,lon" > locations.csv
echo "28.999,-81.001" >> locations.csv
echo "27.7221,-82.7386" >> locations.csv

# Run the command line utility
python3 get_tcwind_csv.py --return_period 100 --location_csv locations.csv  --output_filename DeepCyc_RP_100yr.csv --product DeepCyc
```

After a succesfull execution of `get_hazard_csv.py` utility you can check the results stored in the output file with the following command:

```Bash
cat DeepCyc_RP_100yr.csv
```

Another useful tool is the `get_metryc_footprint.py` script. This allows you to download a Metryc surface wind footprint for any recorded Tropical Cyclone globally. It can write output in either GeoTiff or GeoJSON formats. For example, after setting up the Python environment as above try running:

```Bash
python3 tools/get_metryc_footprint.py --bbox 30 31 -88 -86 --storm_name Dennis --storm_season 2005
```

This should write out a file with a default name `Dennis_2005_FT_3-seconds_kph.tiff` which can be viewed using GIS software such as QGIS.

## Contact

email: nic at reask.earth or fabio at reask.earth
