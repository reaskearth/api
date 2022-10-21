
# Reask API

## Introduction

The Reask API currently supports two products:

1. DeepCyc: a high-resolution probabilistic view of tropical cyclone (TC) risk everywhere in the world, both under the current as well as future climate scenarios.
2. HindCyc: high-resolution tropical cyclone gust footprint estimates for both historical storms and immediately after landfall.

Further information can be found on our website (https://reask.earth/products/).

## API Authentication

The API uses an OpenID Connect (IODC) authentication flow whereby a username and password are used to get an access token, which is then used for subsequent API calls. Please keep your username and password in a secure place.

Example Python code used to get an access token:

```Python
import requests
import json

auth_url = 'https://api.reask.earth/v1/token'
args = {'username': '<MY_USERNAME>',
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

The DeepCyc API has two endpoints:

1. `v1/deepcyc/pointep/`: returns TC surface windspeeds at a requested latitude, longitude point and return period (inverse of the exceedance probability). The windspeeds can be returned as either a terrain-corrected 3-second gust, or an "open water" or "open terrain" corrected 1-minute averaging period. For example:

```Python
url = 'https://api.reask.earth/v1/deepcyc/pointep'
params = {
    'access_token': auth_res['access_token'], # access token from auth step
    'hazard': 'TCWind',
    'epoch': 'PresentDay',
    'latitude': 25.6,
    'longitude': -81.6,
    'years': [10, 100, 250]
}

res = requests.get(url, params=params)
assert res.status_code == 200, 'API GET request failed'
```

Returns:

```Python
{
    "product": "DeepCyc-2.0.3"
    "data": [
        {
            "return_period_year": 10,
            "windspeed_ft_3sec_kph": 136
        },
        {
            "return_period_year": 100,
            "windspeed_ft_3sec_kph": 235
        },
        {
            "return_period_year": 250,
            "windspeed_ft_3sec_kph": 263
        }
    ],
}
```

2. `/deepcyc/v1/gateep/`: returns TC surface windspeeds crossing/entering a gate at a specified return period. The gate can be a single line, a quadrilateral or a circle. The values returned are 1-minute averaged with no terrain correction. For example:

```Python
url = 'https://api.reask.earth/v1/deepcyc/gateep'
params = {
    'access_token': auth_res['access_token'], # access token from auth step
    'hazard': 'TCWind',
    'epoch': 'PresentDay',
    'gate': 'circle'
    'center_latitude': 25.6,
    'center_longitude': -81.6,
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
            "windspeed_nt_1min_kph": 174
        },
        {
            "return_period_year": 50,
            "windspeed_nt_1min_kph": 218
        },
        {
            "return_period_year": 200,
            "windspeed_nt_1min_kph": 261
        }
    ],
    "product": "DeepCyc-2.0.3"
}
```

## HindCyc Usage

The HindCyc API endpoints are similar to DeepCyc:

1. `v1/hindcyc/pointep`: returns estimated TC surface windspeeds at a requested latitude, longitude point for all historical storms within a set of years. The windspeeds can be returned as either a terrain-corrected 3-second gust, or an "open water" or "open terrain" corrected 1-minute averaging period.

2. `v1/hindcyc/gateep`: returns agency recorded TC surface windspeeds crossing/entering a gate. The gate can be a line a quadrilateral or a circle. The values returned are 1-minute averaged.

