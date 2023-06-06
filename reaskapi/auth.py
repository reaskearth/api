
import os.path
import configparser
import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

def get_access_token():
    # Be sure to have a .reask credentials file in your HOME directory!
    # The format of the ~/.reask config containing username and password is:
    #[default]
    #username = <USERNAME_OR_EMAIL>
    #password = <PASSWORD>
    #
    home_dir = os.path.expanduser('~')
    config_file = Path(home_dir) / '.reask'

    config = configparser.ConfigParser()
    config.read(config_file)

    args = {'username': config['default']['username'],
            'password': config['default']['password']}

    auth_url = 'https://api.reask.earth/v1/token'

    # Call the authentication endpoint
    logger.info('Authenticating')
    res = requests.post(auth_url, data=args)

    if res.status_code != 200:
        logger.error(f'Returned HTTP code {res.status_code}')
        logger.info(res.text)
        raise Exception('Authentication failed')

    # Get response as JSON and return the access_token
    auth_res = res.json()

    if 'access_token' not in auth_res:
        logger.error('Access token not found in response')
        logger.debug(auth_res)
        raise Exception('Authentication failed')
    
    logger.debug('Authentication succeeded')

    return auth_res['access_token']

