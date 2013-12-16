import uuid
import webob
import simplejson
from webob.dec import wsgify

class Controller(object):
    def __init__(self):
        self.instances = {}
        for i in xrange(3):
            inst_id = str(uuid.uuid4())
            self.instances[inst_id] = {'id': inst_id, 
                                       'name': 'inst-' + str(i)}

    def create(self, req):
        print(req.params)
        name = req.params['name']
        if name:
            inst_id = str(uuid.uuid4())
            inst = {'id': inst_id, 
                    'name': name}
        
            self.instances[inst_id] = inst
            return {'instance': inst}

    def show(self, req, instance_id):
        inst = self.instances.get(instance_id)
        return {'instance': inst}        

    def index(self, req):
        return {'instances': self.instances.values()}

    def delete(self, req, instance_id):
        if self.instances.get(instance_id):
            self.instances.pop(instance_id)

    def update(self, req, instance_id):
        inst = self.instances.get(instance_id)
        name = req.params['name']
        if inst and name:
            inst['name'] = name
            return {'instance': inst}

    @wsgify(RequestClass=webob.Request)    
    def __call__(self, req):
        arg_dict = req.environ['wsgiorg.routing_args'][1]
        action = arg_dict.pop('action')
        del arg_dict['controller']

        method = getattr(self, action)
        result = method(req, **arg_dict)

        if result is None:
            return webob.Response(body='',
                                  status='204 Not Found',
                                  headerlist=[('Content-Type',
                                               'application/json')])
        else:
            if not isinstance(result, basestring):
                result = simplejson.dumps(result)
            return result

