from webob.dec import wsgify
from webob import exc

@wsgify.middleware
def auth_filter(request, app):
    if request.headers.get('X-Auth-Token') != 'open-sesame':
        return exc.HTTPForbidden()
    return app(request)

def filter_factory(global_config, **local_config):
    return auth_filter

