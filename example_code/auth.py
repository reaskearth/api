
import os
import configparser
import requests
from pathlib import Path

def get_access_token():

    # The format of the ~/.reask config containing username and password is:
    #[default]
    #username = <USERNAME_OR_EMAIL>
    #password = <PASSWORD>
    #
    config_file = Path(os.environ['HOME']) / '.reask'

    config = configparser.ConfigParser()
    config.read(config_file)

    args = {'username': config['default']['username'],
            'password': config['default']['password']}

    auth_url = 'https://api.reask.earth/v1/token'
    res = requests.post(auth_url, data=args)
    assert res.status_code == 200
    auth_res = res.json()

    if 'access_token' not in auth_res:
        print(auth_res)
        return None

    return auth_res['access_token']

