import time

from django.utils.dateparse import parse_datetime
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard import api

from horizon import exceptions

from .test_data import json as test_json


def correlate_tenants(request, instances):
    # Gather our tenants to correlate against IDs
    try:
        tenants = api.keystone.tenant_list(request, admin=True)
    except:
        tenants = []
        msg = _('Unable to retrieve instance tenant information.')
        exceptions.handle(request, msg)
    tenant_dict = SortedDict([(t.id, t) for t in tenants])
    for inst in instances:
        tenant = tenant_dict.get(inst.tenant_id, None)
        inst._apiresource._info['tenant'] = tenant._info
        inst.tenant = tenant


def correlate_flavors(request, instances):
    # Gather our flavors to correlate against IDs
    try:
        flavors = api.nova.flavor_list(request)
    except:
        flavors = []
        msg = _('Unable to retrieve instance size information.')
        exceptions.handle(request, msg)

    flavors_dict = SortedDict([(f.id, f) for f in flavors])
    for inst in instances:
        flavor = flavors_dict.get(inst.flavor["id"], None)
        inst._apiresource._info['flavor'] = flavor._info
        inst.flavor = flavor


def correlate_users(request, instances):
    # Gather our users to correlate against IDs
    try:
        users = api.keystone.user_list(request)
    except:
        users = []
        msg = _('Unable to retrieve instance user information.')
        exceptions.handle(request, msg)
    user_dict = SortedDict([(u.id, u) for u in users])
    for inst in instances:
        user = user_dict.get(inst.user_id, None)
        inst._apiresource._info['user'] = user._info
        inst.user = user


def calculate_ages(instances):
    for instance in instances:
        dt = parse_datetime(instance._apiresource.created)
        timestamp = time.mktime(dt.timetuple())
        instance._apiresource._info['created'] = timestamp
        instance.age = dt


def get_fake_instances_data(request):
    import json
    from novaclient.v1_1.servers import Server, ServerManager
    from horizon.api.nova import Server as HServer
    instances = [HServer(Server(ServerManager(None), i), request)
                 for i in json.loads(test_json)]
    for i in instances:
        i._loaded = True
    instances += instances
    return instances


def get_instances_data(request):
    instances = api.nova.server_list(request, all_tenants=True)

    # Get the useful data... thanks Nova :-P
    if instances:
        correlate_flavors(request, instances)
        correlate_tenants(request, instances)
        correlate_users(request, instances)
        calculate_ages(instances)

    return instances
