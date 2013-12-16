from webob import Response
from webob.dec import wsgify
from paste import httpserver
from paste.deploy import loadapp
import os
import sys

ini_path = os.path.normpath(
             os.path.join(os.path.abspath(sys.argv[0]),
                          os.pardir,
                          'api-paste.ini')
             )

@wsgify
def application(request):
    return Response('Hello, World of WebOb !\n')

def app_factory(global_config, **local_config):
    return application

if not os.path.isfile(ini_path):
    print("Cannot find api-paste.ini.\n")
    exit(1)

wsgi_app = loadapp('config:' + ini_path)
httpserver.serve(wsgi_app, host='127.0.0.1', port=8080)
