from paste import httpserver

def application(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    return ['Hello World\n']

httpserver.serve(application, host='127.0.0.1', port=8080)
