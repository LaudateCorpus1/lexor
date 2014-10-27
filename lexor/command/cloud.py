"""
Here we can find functions to communicate with the cloud to find
lexor packages in Github, register them and delete them.

"""
import os
import six
import json
import textwrap
import httplib
from imp import load_source
from lexor.command import error, disp
from lexor.command import config

DESC = {'main': """
communicate with the cloud. This will allow you to register a style
that is being hosted in Github. You must provide a Github access
token in order to use this command. To create a Github token see:

https://help.github.com/articles/creating-an-access-token-for-command-line-use/

If you wish to avoid typing the Github token you may save the token
to the environmental variable `$GITHUB_ACCESS_TOKEN`.

""", 'register': """
register the style specified by the input file. Make sure that the
style is an existing repository in Github and to provide your Github
access code to the cloud.

""", 'delete': """
delete the style specified by the input file. Make sure that the
style is an existing repository in Github and to provide your Github
access code to the cloud.

""", 'list': """
list available styles.

"""}


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    main = subp.add_parser('cloud', help='communicate with the cloud',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC['main']))
    main.add_argument('--access-token', type=str, dest='token',
                      metavar='TOKEN',
                      help='github access token')

    sub = main.add_subparsers(title='subcommands',
                              dest='subparser_name',
                              help='additional help',
                              metavar='<command>')

    sub.add_parser('register', help='register a style',
                   formatter_class=fclass,
                   description=textwrap.dedent(DESC['register']))

    sub.add_parser('delete', help='register a style',
                   formatter_class=fclass,
                   description=textwrap.dedent(DESC['delete']))

    sub.add_parser('list', help='list available styles',
                   formatter_class=fclass,
                   description=textwrap.dedent(DESC['list']))


def run():
    """Perform a cloud operation. """
    arg = config.CONFIG['arg']
    path = os.path.abspath(arg.inputfile)
    if '.py' not in path:
        path = '%s.py' % path
    try:
        mod = load_source("tmp-mod", path)
    except IOError:
        error("ERROR: Not a valid module.\n")
    if not hasattr(mod, 'INFO'):
        error("ERROR: module does not have `INFO`\n")
    token = ''
    if arg.token:
        token = arg.token
    elif mod.INFO['git']['host'] == 'github':
        token = os.environ.get('GITHUB_ACCESS_TOKEN', '')
    func = {
        'register': _register,
        'delete': _delete,
        'list': _list,
    }
    func[arg.subparser_name](arg, mod.INFO, token)


def _register(_, info, token):
    """Register a style in the cloud. """
    inputs = {
        'style': info['style'],
        'to_lang': str(info['to_lang']),
        'type': info['type'],
        'lang': info['lang'],
        'repo': info['git']['repo'],
        'user': info['git']['user'],
        'host': info['git']['host'],
        'token': token
    }
    ans = cloud_request('register', inputs)
    if isinstance(ans, six.string_types):
        error("ERROR: %s\n" % ans)
    else:
        disp("registration successful:\n")
        for key in ans:
            disp('  %s: %s\n' % (key, ans[key]))


def _delete(_, info, token):
    """Register a style in the cloud. """
    inputs = {
        'repo': info['git']['repo'],
        'user': info['git']['user'],
        'host': info['git']['host'],
        'token': token
    }
    ans = cloud_request('delete', inputs)
    if isinstance(ans, six.string_types):
        error("ERROR: %s\n" % ans)
    else:
        disp("deletion successful:\n")
        for key in ans:
            disp('  %s: %s\n' % (key, ans[key]))


def _list(arg, info, token):
    """List the available styles. """
    inputs = {}
    ans = cloud_request('match', inputs)
    if isinstance(ans, six.string_types):
        error("ERROR: %s\n" % ans)
    else:
        print ans

def cloud_request(request, data):
    """Make a request to the cloud. """
    data = json.dumps(data)
    lexor_key = "aUQhbr8UXCHooj41tY9YtbGyo9L7Uv3yN7sEAPDh"
    rest_api_key = "RQZuvdQexH7HtnJWVWTlREJbWrodiTb2uitSqTLL"
    connection = httplib.HTTPSConnection('api.parse.com', 443)
    connection.connect()
    connection.request('POST', '/1/functions/'+request, data, {
        "X-Parse-Application-Id": lexor_key,
        "X-Parse-REST-API-Key": rest_api_key,
        "Content-Type": "application/json"
    })
    result = json.loads(connection.getresponse().read())
    if 'error' in result:
        return result['error']
    else:
        return result['result']
