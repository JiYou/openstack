from nova.db.sqlalchemy.api import get_session, model_query
from nova.myproject.db import models
from oslo.config import cfg
from sqlalchemy import or_
from nova.openstack.common import timeutils
import datetime

db_opts = [
        cfg.IntOpt('host_down_time',
               default=120,
               help='max time in seconds since last getting cpu info '
                    'for hosts.'),
]

CONF = cfg.CONF
CONF.register_opts(db_opts)

def _filter_down_hosts(query):
    now = timeutils.utcnow()
    last_update = now - datetime.timedelta(seconds=CONF.host_down_time)
    query = query.filter(
               or_(models.MyProjectHost.created_at>last_update,
                   models.MyProjectHost.updated_at>last_update)
            )
    return query
    
def myproject_host_create(context, values):
    host_ref = models.MyProjectHost()
    host_ref.update(values)
    host_ref.save()
    return host_ref

def myproject_host_get(context, host_name, session=None, 
                       check_update = True):
    query = model_query(context, models.MyProjectHost, session=session).\
                     filter_by(host_name=host_name)
    if check_update:
        query = _filter_down_hosts(query)
    return query.first()

def myproject_host_update(context, host_name, values):
    session = get_session()
    with session.begin():
        host_ref = myproject_host_get(context, host_name, 
                                      session=session, 
                                      check_update=False)
        if host_ref:
            host_ref.update(values)
            host_ref.save(session=session)
        else:
            values['host_name'] = host_name
            myproject_host_create(context, values)
    return host_ref

def myproject_host_get_all(context, session=None,
                           check_update = True):
    query = model_query(context, models.MyProjectHost, session=session)
    if check_update:
        query = _filter_down_hosts(query)
    return query.all()

