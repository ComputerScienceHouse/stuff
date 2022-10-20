

from os import getenv
from pprint import pprint
import validators


def get_app_envvar(app, var_name):
    return None if not var_name in app.config else app.config[var_name]


def is_app_debugging(app):
    return get_app_envvar(app, 'DEBUG') or get_app_envvar(app, 'TESTING')


def verify_environment(print_results=False):
    """
    Verifies the various environment variables required for app operation.

    Improperly (un)set boolean values will default to False.
    """
    def _as_bool(input):
        return True if type(input) == str and input.lower().strip() == 'true' else False
    # URL where game thumbnails are hosted
    IMAGE_URL = getenv('IMAGE_URL')
    # Set to whatever 'Stuff` database will be called
    MONGODB_DATABASE = getenv('MONGODB_DATABASE')
    # Set to anything, but keep it a secret
    SECRET_KEY = getenv('SECRET_KEY')
    # Set to `http` for CSH auth
    PREFERRED_URL_SCHEME = getenv('URL_SCHEME', 'http')
    # Set to localhost:5000 for use with CSH auth
    SERVER_NAME = getenv('SERVER_NAME', 'localhost:5000')

    ''' OIDC '''
    OIDC_CLIENT_ID = getenv('OIDC_CLIENT_ID')
    OIDC_CLIENT_SECRET = getenv('OIDC_CLIENT_SECRET')
    OIDC_ISSUER = getenv('OIDC_ISSUER')

    ''' S3 '''
    S3_BUCKET = getenv('S3_BUCKET')
    S3_KEY = getenv('S3_KEY')
    S3_SECRET = getenv('S3_SECRET')
    S3_ENDPOINT = getenv('S3_ENDPOINT')

    ''' The below environment variables exist, but do not need to be set/modified '''
    WTF_CSRF_ENABLED = _as_bool(getenv('WTF_CSRF_ENABLED', False))
    comb_server_url = f'{PREFERRED_URL_SCHEME}://{SERVER_NAME}'
    tests = {'IMAGE_URL': validators.url(IMAGE_URL),
             'MONGODB_DATABASE': validators.truthy(MONGODB_DATABASE),
             'SECRET_KEY': validators.truthy(SECRET_KEY),
             'IMAGE_URL': validators.truthy(IMAGE_URL),
             '{PREFERRED_URL_SCHEME}://{SERVER_NAME}':
             True if validators.url(comb_server_url)
             else 'False (the combination of PREFERRED_URL_SCHEME and SERVER_NAME appears to be an invalid url...)',
             'OIDC_CLIENT_ID': validators.truthy(OIDC_CLIENT_ID),
             'OIDC_CLIENT_SECRET': validators.truthy(OIDC_CLIENT_SECRET),
             'OIDC_ISSUER': validators.truthy(OIDC_ISSUER),
             'S3_BUCKET': validators.truthy(S3_BUCKET),
             'S3_KEY': validators.truthy(S3_KEY),
             'S3_SECRET': validators.truthy(S3_SECRET),
             'S3_ENDPOINT': validators.truthy(S3_ENDPOINT)}
    if print_results:
        print('Environment verification results: ')
        pprint(tests)
    return tests


if __name__ == '__main__':
    verify_environment(print_results=True)
