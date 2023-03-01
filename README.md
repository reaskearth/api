
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
python3 ./deepcyc_pointep.py
python3 ./deepcyc_gateep.py
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

The DeepCyc API has four endpoints **pointep**, **gateep**, **point** and **gate**.

### PointEP (Point Exceedance Probability)

`v1/deepcyc/pointep` returns TC surface windspeeds at a requested latitude, longitude point and return period (inverse of the exceedance probability). The windspeeds can be returned as either a terrain-corrected 3-second gust, or an "open water" or "open terrain" corrected 1-minute averaging period. For example:

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
- `cell_latitude` and `cell_longitude`: the center point of the cell that encompasses the requested location. Reask uses a global, regular lat, lon grid with roughly 1km resolution for all wind hazard products. Given this resolution the cell coordinates returned will never be more than around 700m from the requested location.
- `return_period_year`: the return period of the given windspeed.
- `windspeed_ft_3sec_kph`: the windspeed value for the given location and return period. In this case the value is terrain-corrected 3-second gust in units of kilometers per hour.

If a requested location is not available, e.g because it is not considered at risk or outside the allowed region, then the API request will still succeed but the values returned with will `NA` and a `message` field will provide some explanation.

### GateEP (Gate Exceedance Probability)

`v1/deepcyc/gateep` returns TC maximum surface windspeeds crossing/entering a gate at a specified return period. The gate can be a line, a polygon or a circle. The values returned are 1-minute averaged with no terrain correction. For example:

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

- `circle`: requires a single `lat` and `lon` point representing the centre as well as a `radius_km`.
- `polygon`: requires a list of `lat` and `lon` pairs representing the corners of the shape. The first and last points must be the same.
- `line`: requires two or more points representing a multi-segment line. The example code (https://github.com/reaskearth/api/blob/main/example_code/gate_ep.py) shows a line following the coast around New Orleans, USA.

### Point

`v1/deepcyc/point` returns maximum TC surface windspeeds of all (synthetic) events impacting a given latitude, longitude point during the given epoch. The windspeeds can be returned as either a terrain-corrected 3-second gust, or an "open water" or "open terrain" corrected 1-minute averaging period. For example:


```Python
url = 'https://api.reask.earth/v1/deepcyc/point'
params = {
    'access_token': auth_res['access_token'], # access token from auth step
    'peril': 'TC_Wind',
    'tag': 'Miami Beach',
    'epoch': 'Present_Day',
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
            "latitude:": 25.80665,
            "longitude:" -80.12412,
            "cell_latitude": 25.8056640625,
            "cell_longitude": -80.1318359375,
            "year_id": 2013_0117_1051,
            "event_id": FU_NV_i2.0.5__FBHEPR_YRAF2__RAF_1051.003__Onfva_NV__FhoErtvba_12__Frnfba_2013__Fnzcyr_0117__Genpx_00000008
            "windspeed_ft_3sec_kph": 128
        },
        {
            "latitude:": 25.80665,
            "longitude:" -80.12412,
            "cell_latitude": 25.8056640625,
            "cell_longitude": -80.1318359375,
            "year_id": 2012_0086_1111,
            "event_id": FU_NV_i2.0.5__FBHEPR_YRAF2__RAF_1111.006__Onfva_NV__FhoErtvba_12__Frnfba_2012__Fnzcyr_0086__Genpx_00000008,
            "windspeed_ft_3sec_kph": 212
        },
        {
            "latitude:": 25.80665,
            "longitude:" -80.12412,
            "cell_latitude": 25.8056640625,
            "cell_longitude": -80.1318359375,
            "year_id": 2015_0021_1131,
            "event_id": FU_NV_i2.0.5__FBHEPR_YRAF2__RAF_1131.007__Onfva_NV__FhoErtvba_12__Frnfba_2015__Fnzcyr_0021__Genpx_00000005,
            "windspeed_ft_3sec_kph": 237
        }
        ...
    ],
    "epoch": "Present_Day",
    "product": "DeepCyc-2.0.5",
    "simulation_years": 20000,
    "tag": "Miami Beach"
}
```

Not that the above list has been shortened.


### Gate

`v1/deepcyc/gate` returns TC maximum surface windspeeds for all events crossing or within a gate during a given epoch. The gate can be a line, a polygon or a circle. The values returned are 1-minute averaged with no terrain correction. For example:

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
        {
            "windspeed_nt_1min_kph": 197
            "year_id": 2019_0175_1301,
            "event_id": FU_NH_i2.0.5__FBHEPR_YRAF2__RAF_1301.020__Onfva_NH__FhoErtvba_13__Frnfba_2019__Fnzcyr_0175__Genpx_00000001
        },
        {
            "windspeed_nt_1min_kph": 234
            "year_id": 2015_0021_1131,
            "event_id": FU_NV_i2.0.5__FBHEPR_YRAF2__RAF_1131.007__Onfva_NV__FhoErtvba_12__Frnfba_2015__Fnzcyr_0021__Genpx_00000005
        },

        ...
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
