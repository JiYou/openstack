from webob import Response
from webob.dec import wsgify
from webob import exc
import webob

class Auth(object):

    def __init__(self, app):
        self.app = app

    @classmethod
    def factory(cls, global_config, **local_config):
        def _factory(app):
            return cls(app)
        return _factory

    @wsgify(RequestClass=webob.Request)
    def __call__(self, req):
        resp = self.process_request(req)
        if resp:
            return resp
        return req.get_response(self.app)

    def process_request(self, req):
        if req.headers.get('X-Auth-Token') != 'open-sesame':
            return exc.HTTPForbidden()
   
