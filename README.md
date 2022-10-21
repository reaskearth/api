
# Reask API

## Introduction

The Reask API currently supports two products:

1. DeepCyc: high-resolution probabilistic view of tropical cyclone (TC) risk everywhere in the world, both under the current as well as future climate scenarios.
2. HindCyc: high-resolution probabilistic tropical cyclone gust footprints both for historical storms and immediately after landfall.

The Reask Map API base URL is: `https://api.reask.earth`

Further information can be found on our website (https://reask.earth/products/).

## API Authentication

The API uses an OpenID Connect (IODC) authentication flow whereby a username and password are used to get an access token which is then used for subsequent API calls. Please keep your username and password in a secure place.

Example code used to get an access token:

```Python
import requests
import json

auth_url = 'https://api.reask.earth/token'
args = {'username': '<MY_USERNAME>',
        'password': '<MY_PASSWORD>'}
res = requests.post(auth_url, data=args)

assert res.status_code == 200, 'Login failed'
print(json.dumps(res.json, ident=4))
```

## DeepCyc Usage

The DeepCyc API has two endpoints:

1. `/deepcyc/v1/pointep/`: returns TC surface windspeeds at a requested latitude, longitude point and return period (inverse of the exceedance probability). The windspeeds can be returned as either a terrain-corrected 3-second gust, or an "open water" or "open terrain" corrected 1-minute averaging period.

2. `/deepcyc/v1/gateep/`: returns TC surface windspeeds crossing/entering a gate at a specified return period. The gate can be a single line or a more complex shape such as a circle or square. The values returned are 1-minute averaged with no terrain correction.


## HindCyc Usage

The HindCyc API endpoints are similar to DeepCyc, there are two endpoints:

1. `/hindcyc/v1/pointep`:

2. `/hindcyc/v1/pointep`:
