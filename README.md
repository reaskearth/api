
# Reask API

## Introduction

The Reask API currently supports two products:

1. DeepCyc: a high-resolution probabilistic view of tropical cyclone (TC) risk everywhere in the world, both under current as well as future climate scenarios.
2. Metryc: high-resolution tropical cyclone (TC) windspeed estimates for historical events based on our ML windfield model and incorporating agency best track data.

Further information can be found on our website (https://reask.earth/products/).

An up-to-date version of this README can be found here: https://github.com/reaskearth/api/blob/main/README.md

## Package Status

| Branch | Status |
|--------|--------|
| main | [![Build Status](https://github.com/reaskearth/api/actions/workflows/github-actions-ci.yaml/badge.svg)](https://github.com/reaskearth/api/actions/workflows/github-actions-ci.yaml) |

##<a name="quickstart"></a> Quickstart

Put your Reask credentials into a file called `.reask` in your home directory using the following format:

```
[default]
username = <USERNAME_OR_EMAIL>
password = <PASSWORD>
```

Check the permissions of this file and make sure it is only readable by yourself by running the following command:

```
chmod 600 ~/.reask
```

### Source code
Take a look at the Python3 example code here: https://github.com/reaskearth/api/.

This can be downloaded by either clicking on the green **Code** button or using the `git` command as follows:

```
git clone https://github.com/reaskearth/api.git reaskapi
```

Once downloaded you can test the code by running some of the examples under the `example_code` folder:

```
cd reaskapi/example_code
python3 ./deepcyc_point.py
python3 ./deepcyc_pointaep.py
```

This should leave a `.json` file in the current directory containing the results.

## API Authentication

The API uses an OpenID Connect (IODC) authentication flow whereby a username/email and password are used to get an access token, which is then used for subsequent API calls. Please keep your password in a secure place.

Example Python code used to get an access token:

```Python
import requests
import json

auth_url = 'https://api.reask.earth/v1/token'
args = {'username': '<MY_USERNAME_OR_EMAIL>',
        'password': '<MY_PASSWORD>'}
res = requests.post(auth_url, data=args)

assert res.status_code == 200, 'Login failed'
print(json.dumps(res.json(), indent=4))
```

Will output:

```
{
    "access_token": "<ACCESS_TOKEN>",
    "expires_in": 3600,
    ...
}
```

The `access_token` value is then used as a `GET` request parameter as shown in the following code snippets. The example code (https://github.com/reaskearth/api/blob/main/example_code/auth.py) demonstrates how to use credentials which are stored in a hidden file.


## API Tools Usage

The `tools/` directory contains some command line utilities that make it easy to use the API for common tasks.

*get_hazard_csv.py*: will generate a CSV containing hazard values for provided locations in a CSV file. It supports both DeepCyc for probabilistic risk as well as Metrcy for estimates of historical events.

The CSV file should include a header line with the latitude and longitude columns. The tool accepts the following column names:

- latitude: `latitude`, `Latitude`, `lat`, or `Lat`
- longitude: `longitude`, `Longitude`, `lon`, or `Lon`

To use `get_hazard_csv.py` first set-up the authentication and clone the repository as described in the [Quickstart](#quickstart) section and then try the following sequence of commands from the directory where the code is located in your computer:

```Bash
# Change the current directory to the tools folder
cd tools

# Create a locations.csv file with the points of interest.
# This will create a locations file with three spoints
echo "lat,lon" > locations.csv
echo "28.999,-81.001" >> locations.csv
echo "27.7221,-82.7386" >> locations.csv
echo "26.26,-83.51" >> locations.csv

# Run the command line utility
python3 get_hazard_csv.py --rp_year 20 --location_csv locations.csv  --output_filename DeepCyc_RP20y.csv --product DeepCyc
```

After a succesfull execution of `get_hazard_csv.py` utility you can check the results stored in the output file with the following command:

```Bash
cat DeepCyc_RP20y.csv
```


## DeepCyc Endpoint Usage

The DeepCyc API has four endpoints **point**, **pointaep**, **gate** and **gateaep**.

### Point

`v1/deepcyc/point` returns maximum TC surface windspeeds of all (synthetic) events impacting a given latitude, longitude point during the given epoch. The windspeeds can be returned with a range of different terrain corrections:

- `FT_GUST`: Full Terrain 3-second gust correction. Uses our ML terrain correction algorithm to calculate over-land gust depending on such things as land-use, topography, wind direction etc.
- `OW`: Open Water. No correction is applied.
- `NT`: No Terrain. As above, no correction is applied.
- `OT`: Open Terrain. An flat grassland correction is applied.

In addition either a `3-second` or `1-minute` wind averaging period can be selected. For the `ft_gust` terrain type only `3-second` wind averaging is supported.

For example:

```Python
url = 'https://api.reask.earth/v1/deepcyc/point'
params = {
    'access_token': auth_res['access_token'], # access token from auth step
    'peril': 'TC_Wind',
    'epoch': 'Present_Day',
    'terrain_correction': 'FT_GUST',
    'windspeed_averaging_period': '3-seconds',
    'units': 'mph',
    'lats': [26.26],
    'lons': [-83.51],
}

res = requests.get(url, params=params)
assert res.status_code == 200, 'API GET request failed'
```

Returns:

```Python
{
    "features": [
        {
            "geometry": {
                "coordinates": [
                    [
                        ...
                    ]
                ],
                "type": "Polygon"
            },
            "properties": {
                "cell_id": 438894232,
                "event_ids": [
                    "96e41f9553fb059d2bb1",
                    ...
                    "7dd6a559764dd9a21455"
                ],
                "latitude": 26.26,
                "longitude": -83.51,
                "windspeeds": [
                    250.0,
                    ...
                    37.0
                ],
                "year_ids": [
                    "1998_0664_RAN",
                    ...
                    "1980_0020_RAN"
                ]
            },
            "type": "Feature"
        }
    ],
    "header": {
        "epoch": "Present_Day",
        "product": "DeepCyc-2.0.6",
        "simulation_years": 41000,
        "terrain_correction": "FT_GUST",
        "units": "mph",
        "wind_averaing_period": "3-seconds"
    },
    "type": "FeatureCollection"
}
```

The returned document is a valid [GeoJSON](https://en.wikipedia.org/wiki/GeoJSON) document describing the geometry of the requested locations (also known as `features`).

The `properties` attribute of each feature contains the following fields:

- `cell_id`: this is a globally unique identifier for the returned grid cell. There is example code showing how to map these ids to and from cells at `example_code/grid_cell_id_map.py`.
- `event_ids`: a list of identifiers for the events that have impacted the requested location.
- `windspeeds`: the maximum windspeeds of the aforementioned events at the requested location.
- `years_ids`: the identifiers of the synthetic years in which the aforementioned events occur.


### Point AEP (Annual Exceedance Probability)

`v1/deepcyc/pointaep` returns TC surface windspeeds at a requested latitude, longitude point and annual exceedance probability. It can also return an AEP from requested windspeeds. As with the `point` endpoint the windspeeds can be returned as either different terrain corrections, wind averaging periods and units.

For example to request windspeeds at AEPs of 0.1, 0.01, 0.004:

```Python
url = 'https://api.reask.earth/v1/deepcyc/pointep'
params = {
    'access_token': auth_res['access_token'], # access token from auth step
    'peril': 'TC_Wind',
    'tag': 'Miami Beach',
    'epoch': 'Present_Day',
    'lats': [25.80665],
    'lons': [-80.12412],
    'aeps': [0.1, 0.01, 0.004]
}

res = requests.get(url, params=params)
assert res.status_code == 200, 'API GET request failed'
```

Or, equivalently for annual return periods of 10, 100, 250 years:
```
del params['aeps']
params['years'] = [10, 100, 250]
res = requests.get(url, params=params)
```

Returns:

```Python
{
    "header": {
        "epoch": "Present_Day",
        "product": "DeepCyc-2.0.6",
        "simulation_years": 41000,
        "tag": "Florida",
        "terrain_correction": "ft_gust",
        "units": "kph",
        "windspeed_averaing_period": "3-seconds"
    },
    "type": "FeatureCollection"
    "features": [
    {
        "geometry": {
            "coordinates": [
                ...
            ],
            "type": "Polygon"
        },
        "properties": {
            "cell_id": 438710150,
            "aeps": [
                0.1,
                0.01,
                0.004
            ],
            "windspeeds": [
                119.0,
                200.0,
                223.0
            ]
        },
   }],
}
```

The example code includes a request for the AEPs at given windspeeds.


### Gate

`v1/deepcyc/gate` returns TC maximum surface windspeeds for all events crossing or within a gate during a given epoch. The gate can be a line, a polygon or a circle. The values returned are 1-minute averaged with no terrain correction / open water. For example:

```Python
url = 'https://api.reask.earth/v1/deepcyc/gate'
params = {
    'access_token': auth_res['access_token'], # access token from auth step
    'peril': 'TC_Wind',
    'epoch': 'Present_Day',
    'gate': 'circle'
    'lats': [30],
    'lons': [-90.0],
    'radius_km': 50,
}

res = requests.get(url, params=params)
assert res.status_code == 200, 'API GET request failed'
```

### Gate AEP (Gate Annual Exceedance Probability)

`v1/deepcyc/gateaep` returns TC maximum surface windspeeds crossing/entering a gate at a specified annual exceedance probability. The gate can be a line, a polygon or a circle. The values returned are 1-minute averaged with no terrain correction. For example:

```Python
url = 'https://api.reask.earth/v1/deepcyc/gateep'
params = {
    'access_token': auth_res['access_token'], # access token from auth step
    'peril': 'TC_Wind',
    'epoch': 'Present_Day',
    'gate': 'circle'
    'lats': [30],
    'lons': [-90.0],
    'radius_km': 50,
    'aeps': [0.05, 0.02, 0.005]
}

res = requests.get(url, params=params)
assert res.status_code == 200, 'API GET request failed'
```

## Metryc Endpoint Usage

The Metryc API supports **point** and **gate** endpoints.

### Point

`v1/metryc/point` returns estimated TC surface windspeeds at a requested latitude, longitude point for all historical storms within a set of years. The windspeeds can be returned as either a terrain-corrected 3-second gust, or an "open water" or "open terrain" corrected 1-minute averaging period. Currently only the period 1980 to 2022 is supported. For example:


```Python
url = 'https://api.reask.earth/v1/metryc/point'
params = {
    'access_token': auth_res['access_token'], # access token from auth step
    'peril': 'TC_Wind',
    'tag': 'Miami Beach',
    'lats': [25.80665],
    'lons': [-80.12412],
}

res = requests.get(url, params=params)
assert res.status_code == 200, 'API GET request failed'
```

Returns:

```Python
    {
        "data": [
            {
                "latitude": 25.80665,
                "longitude": -80.13412,
                "storm": "Charley_2004",
                "windspeed_ft_3sec_kph": 99
            },
            {
                "latitude": 25.80665,
                "longitude": -80.13412,
                "storm": "Katrina_2005",
                "windspeed_ft_3sec_kph": 107
            },
            {
                "latitude": 25.80665,
                "longitude": -80.13412,
                "storm": "Ian_2022",
                "windspeed_ft_3sec_kph": 90
            },
            {
                "latitude": 25.80665,
                "longitude": -80.13412,
                "storm": "Wilma_2005",
                "windspeed_ft_3sec_kph": 159
            },
            {
                "latitude": 25.80665,
                "longitude": -80.13412,
                "storm": "Andrew_1992",
                "windspeed_ft_3sec_kph": 263
            },

            ...
        ],
        "product": "Metryc-2.0.1",
        "reporting_period": "1980 to 2021",
        "tag": "Miami Beach"
    }
```

Not that the above list has been shortened.

### Gate

`v1/metryc/gate` returns agency recorded TC surface windspeeds entering or within a gate. The values returned are 1-minute averaged and the underlying dataset used is IBTrACS (https://www.ncei.noaa.gov/products/international-best-track-archive). You can think of this endpoint as an alternative way to query the IBTrACS database and it is useful for comparing the Reask products with observed TC risk.

## Contact

email: nic at reask.earth
