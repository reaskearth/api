
# Reask API

## Introduction

The Reask API currently supports two products:

1. DeepCyc: a high-resolution probabilistic view of tropical cyclone (TC) risk everywhere in the world, both under current as well as future climate scenarios.
2. Metryc: high-resolution tropical cyclone (TC) windspeed estimates for historical events based on our ML windfield model and incorporating agency best track data.

Further information can be found on our website (https://reask.earth/products/).

An up-to-date version of this README can be found here: https://github.com/reaskearth/api/blob/main/README.md

## Quickstart

Put your Reask credentials into a file called `.reask` in your home directory using the following format:

```
[default]
username = <USERNAME_OR_EMAIL>
password = <PASSWORD>
```

Check the permissions of this file and make sure it is only readable by yourself.

Take a look at the Python3 example code here: https://github.com/reaskearth/api/ . This can be downloaded by either clicking on the green **Code** button or using the `git` command as follows:

```
git clone https://github.com/reaskearth/api.git reask-api
```

Once downloaded it can be run with:

```
cd reask-api/example_code
python3 ./deepcyc_point.py
python3 ./deepcyc_pointaep.py
python3 ./deepcyc_gateaep.py
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
print(json.dumps(res.json, indent=4))
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

## DeepCyc Usage

The DeepCyc API has four endpoints **point**, **gate**, **pointaep** and **gateaep**.

### Point

`v1/deepcyc/point` returns maximum TC surface windspeeds of all (synthetic) events impacting a given latitude, longitude point during the given epoch. The windspeeds can be returned with a range of different terrain corrections:

- `ft_gust`: Full Terrain 3-second gust correction. Uses our ML terrain correction algorithm to calculate over-land gust depending on such things as land-use, topography, wind direction etc.
- `ow`: Open Water. No correction is applied.
- `nt`: No Terrain. As above, no correction is applied.
- `ot`: Open Terrain. An flat grassland correction is applied.

In addition either a `3-second` or `1-minute` wind averaging period can be selected. For the `ft_gust` terrain type only `3-second` wind averaging is supported.

For example:

```Python
url = 'https://api.reask.earth/v1/deepcyc/point'
params = {
    'access_token': auth_res['access_token'], # access token from auth step
    'peril': 'TC_Wind',
    'epoch': 'Present_Day',
    'terrain_correction': 'ft_gust',
    'wind_averaging_period': '3-seconds',
    'units': 'mph',
    'lats': [25.8],
    'lons': [-79.5],
}

res = requests.get(url, params=params)
assert res.status_code == 200, 'API GET request failed'
```

Returns:

```Python
{
    "epoch": "Present_Day",
    "product": "DeepCyc-2.0.6",
    "simulation_years": 40500,
    "terrain_correction": "ft_gust",
    "units": "mph",
    "wind_averaing_period": "3-second",
    "data": [
        {
            "latitude": 25.8,
            "longitude": -79.5
            "cell_latitude": 25.7958984375,
            "cell_longitude": -79.4970703125,
            "events": {
                "event_ids": [
                    "850e65031871c7cdd56d",
                    "25f9b79f2cff331a6fe3",
                    "74f1cf4ffb7a51fa62bb",
                    ...
                 ]
                 "year_ids": [
                    "1980_0211",
                    "1981_0107",
                    "1981_0330",
                    ...
                 ]
                 "windspeeds": [
                    37.28226,
                    37.28226,
                    37.28226,
                    ...
                 ]
            }
        }
    ],
}
```

Not that the above list has been shortened.


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

Returns:

```Python
{
    "data": [
        "events": {
            "event_ids": [
                "766d200e57773b36c5ad",
                ...
             ]
             "year_ids": [
                "2019_0175",
                ...
             ]
             "windspeeds": [
                67.28226,
                ...
             ]
        }
    ],
    "epoch": "Present_Day",
    "gate": "circle",
    "lats": [
        29.0
    ],
    "lons": [
        -90.0
    ],
    "wind_averaging_period": "1-minute",
    "terrain_correction": "ow",
    "product": "DeepCyc-2.0.3",
    "radius_km": 50.0,
    "units": "kmh",
    "simulation_years": 20000
}
```


### Point AEP (Point Annual Exceedance Probability)

`v1/deepcyc/pointaep` returns TC surface windspeeds at a requested latitude, longitude point and annual exceedance probability. As with the `point` endpoint the windspeeds can be returned as either different terrain corrections, wind averaging periods and units.

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

Returns:

```Python
{
    "data": [
        {
            "latitude:": 25.80665,
            "longitude:" -80.12412,
            "cell_latitude": 25.8056640625,
            "cell_longitude": -80.1318359375,
            "aep": 0.1,
            "windspeed": 128
        },
        {
            "latitude:": 25.80665,
            "longitude:" -80.12412,
            "cell_latitude": 25.8056640625,
            "cell_longitude": -80.1318359375,
            "aep": 0.01,
            "windspeed": 212
        },
        {
            "latitude:": 25.80665,
            "longitude:" -80.12412,
            "cell_latitude": 25.8056640625,
            "cell_longitude": -80.1318359375,
            "aep": 0.004,
            "windspeed": 237
        }
    ],
    "epoch": "Present_Day",
    "product": "DeepCyc-2.0.5",
    "simulation_years": 20000,
    "tag": "Miami Beach"
}
```

Since the API supports providing lists of both requested return periods and locations the data returned is in the form of a list with items corrosponding to the requested parameters. Each list item has the following fields:

- `latitude` and `longitude`: the latitude and longitude of the requested location.
- `cell_latitude` and `cell_longitude`: the center point of the cell that encompasses the requested location. Reask uses a global, regular lat, lon grid with roughly 1km resolution for all wind hazard products. Given this resolution the cell coordinates returned will never be more than around 700m from the requested location.
- `aep`: the annual exceedance probability of the given windspeed.
- `windspeed`: the windspeed value for the given location and return period.
- `terrrain_correction`: terrain correction used.
- `wind_averaging_period`

If a requested location is not available, e.g because it is not considered at risk or outside the allowed region, then the API request will still succeed but the values returned with will `NA` and a `message` field will provide some explanation.

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

Returns:

```Python
{
    "data": [
        {
            "aep": 0.05,
            "windspeed": 197
        },
        {
            "aep": 0.02,
            "windspeed": 234
        },
        {
            "aep": 0.005,
            "windspeed": 256
        }
    ],
    "epoch": "Present_Day",
    "gate": "circle",
    "lats": [
        29.0
    ],
    "lons": [
        -90.0
    ],
    "product": "DeepCyc-2.0.3",
    "radius_km": 50.0,
    "simulation_years": 20000
}
```

The parameters provided depend on the 'gate' type. They are as follows:

- `circle`: requires a single `lat` and `lon` point representing the centre as well as a `radius_km`.
- `polygon`: requires a list of `lat` and `lon` pairs representing the corners of the shape. The first and last points must be the same.
- `line`: requires two or more points representing a multi-segment line. The example code (https://github.com/reaskearth/api/blob/main/example_code/gate_ep.py) shows a line following the coast around New Orleans, USA.


## Metryc Usage

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
