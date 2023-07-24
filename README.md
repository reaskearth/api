
# Reask API Client

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

## OpenAPI Documentation

The interactive documentation can be found here: https://api.reask.earth/v2/docs. This 

## Quickstart

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
python3 ./deepcyc_tcwind_returnvalue.py
python3 ./metryc_tcwind_events.py
```

This should leave a `.json` or `.csv` file in the current directory containing the results.


## Authentication

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


## Tools Usage

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

## Endpoint Usage

Summary documentation for the DeepCyc and Metryc API endpoints can be found here: https://api.reask.earth/v2/docs

## Contact

email: nic at reask.earth or fabio at reask.earth
