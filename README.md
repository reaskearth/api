
# Reask API

## Introduction

The Reask API currently supports two products:

1. DeepCyc: a high-resolution probabilistic view of tropical cyclone (TC) risk everywhere in the world, both under the current as well as future climate scenarios.
2. HindCyc: high-resolution tropical cyclone gust footprint estimates for both historical storms and immediately after landfall.

Further information can be found on our website (https://reask.earth/products/).

An up-to-date version of this ReadMe can be found here: https://github.com/reaskearth/api/blob/main/README.md

Example code Python3 is here https://github.com/reaskearth/api/blob/main/example_code/ . And if you have a Reask account, can be run with:

```
git clone https://github.com/reaskearth/api.git reask-api
cd reask-api/example_code
python3 ./point_ep.py
python3 ./gate_ep.py
```

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

The `access_token` value is then used as a `GET` request parameter as shown below.

## DeepCyc Usage

The DeepCyc API has two endpoints pointep and gateep.

### PointEP

`v1/deepcyc/pointep/` returns TC surface windspeeds at a requested latitude, longitude point and return period (inverse of the exceedance probability). The windspeeds can be returned as either a terrain-corrected 3-second gust, or an "open water" or "open terrain" corrected 1-minute averaging period. For example:

```Python
url = 'https://api.reask.earth/v1/deepcyc/pointep'
params = {
    'access_token': auth_res['access_token'], # access token from auth step
    'peril': 'TC_Wind',
    'tag': 'Miami Beach',
    'epoch': 'Present_Day',
    'lats': [25.80665],
    'lons': [-80.12412],
    'years': [10, 100, 250]
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
            "return_period_year": 10,
            "windspeed_ft_3sec_kph": 128
        },
        {
            "latitude:": 25.80665,
            "longitude:" -80.12412,
            "cell_latitude": 25.8056640625,
            "cell_longitude": -80.1318359375,
            "return_period_year": 100,
            "windspeed_ft_3sec_kph": 212
        },
        {
            "latitude:": 25.80665,
            "longitude:" -80.12412,
            "cell_latitude": 25.8056640625,
            "cell_longitude": -80.1318359375,
            "return_period_year": 250,
            "windspeed_ft_3sec_kph": 237
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
- `cell_latitude` and `cell_longitude`: the center point of the cell that encompasses the requested location. Reask uses a global, regular lat, lon grid with roughly 1km resolution so the cell coordinates returned will not be more than around 700m from the requested location.
- `return_period_year`: the return period of the given windspeed.
- `windspeed_ft_3sec_kph`: the windspeed value for the given location and return period. In this case the value is terrain-corrected 3-second gust in units of kilometers per hour.

### GateEP

`/deepcyc/v1/gateep/` returns TC surface windspeeds crossing/entering a gate at a specified return period. The gate can be a line, a rectangle or a circle. The values returned are 1-minute averaged with no terrain correction. For example:

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
    'years': [20, 50, 200]
}

res = requests.get(url, params=params)
assert res.status_code == 200, 'API GET request failed'
```

Returns:

```Python
{
    "data": [
        {
            "return_period_year": 20,
            "windspeed_nt_1min_kph": 197
        },
        {
            "return_period_year": 50,
            "windspeed_nt_1min_kph": 234
        },
        {
            "return_period_year": 100,
            "windspeed_nt_1min_kph": 256
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

circle: requires a single `lat` and `lon` point representing the centre as well as a `radius_km`.
rectangle: requires a pair of `lat` and `lon` representing the bottom left and top right corners in that order.
line: requires two or more points representing a multi-segment line. The example code shows a line following the coast around New Orleans, USA.

## HindCyc Usage

The HindCyc API endpoints are similar to DeepCyc.

### PointEP

`v1/hindcyc/pointep` returns estimated TC surface windspeeds at a requested latitude, longitude point for all historical storms within a set of years. The windspeeds can be returned as either a terrain-corrected 3-second gust, or an "open water" or "open terrain" corrected 1-minute averaging period. For example:


```Python
url = 'https://api.reask.earth/v1/hindcyc/pointep'
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

```
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
        "product": "HindCyc-2.0.1",
        "reporting_period": "1980 to 2021",
        "tag": "Miami Beach"
    }
```

Not that the above list has been shortened.

### GateEP

`v1/hindcyc/gateep` returns agency recorded TC surface windspeeds crossing/entering a gate. The gate can be a line a quadrilateral or a circle. The values returned are 1-minute averaged.


## Contact

email: nic at reask.earth
