import json
import httplib


def get(endpoint):
    """Make a get request to github. """
    connection = httplib.HTTPSConnection('api.github.com')
    connection.connect()
    connection.request('GET', endpoint, headers={
        'User-Agent': 'lexor'
    })
    return json.loads(connection.getresponse().read())
