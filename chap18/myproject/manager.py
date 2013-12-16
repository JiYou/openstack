from nova import manager
from nova.openstack.common import log as logging
from oslo.config import cfg
from nova.myproject import db


LOG = logging.getLogger(__name__)

myproject_opts = [
    cfg.IntOpt('txt_timer_interval',
               default=60,
               help='time of interval in senconds to wait for updating cpu info'),
]


CONF = cfg.CONF
CONF.register_opts(myproject_opts)

class MyProjectManager(manager.Manager):

    def __init__(self, *args, **kwargs):
        # 19.4.1
        LOG.info('nova-myproject manager is initialized!')

        # 19.4.3
        self.cpu_info1 = {'total':0, 'idle':0}
        self.cpu_info2 = {'total':0, 'idle':0}
        

    # 19.4.2
    
    def _get_proc_stat(self):
        try:
            f = open('/proc/stat')
            return f.readlines()
        except IOError as exn:
            LOG.error('Failed to read /proc/stat: %s' % exn)
        finally:
            f.close()

    def _get_cpu_usage(self):
        proc_stat = self._get_proc_stat()
        if not proc_stat:
            return

        cols = proc_stat[0].split()
        idle = float(cols[4])
        total = 0
        for col in cols[1:]:
            total += float(col) 

        return {'total': total, 'idle': idle}

    def get_cpu_usage(self, context):
        usage = self._get_cpu_usage()
        if usage:
            idle = usage['idle']
            total = usage['total']
            return {'usage': 100 - idle * 100 / total}
        else:
            return {'usage': 0}

    # 19.4.3

    @manager.periodic_task(spacing=CONF.txt_timer_interval)
    def update_cpu_info(self, context):
        LOG.info('updating cpu info...')
        
        cpu_info = self._get_cpu_usage()
        if cpu_info:
            self.cpu_info1 = self.cpu_info2
            self.cpu_info2 = cpu_info

    def get_cpu_usage2(self, context):
        cpu_info1, cpu_info2 = self.cpu_info1, self.cpu_info2
        total = cpu_info2['total'] - cpu_info1['total']
        idle = cpu_info2['idle'] - cpu_info1['idle']

        if total > 1:
            return {'usage': 100 - idle * 100 / total}
        else:
            return {'usage': 0}

   # 19.4.4

    @manager.periodic_task(spacing=CONF.txt_timer_interval)
    def update_cpu_usage(self, context):
        cpu_usage = self.get_cpu_usage2(context)
        if cpu_usage['usage'] > 0.00001:
            values = {'cpu_usage': cpu_usage['usage']}
            db.myproject_host_update(context, CONF.host, values)
            LOG.info('Finished updating cpu usage into database.')

    def get_all_cpu_usage(self, context):
        host_list = db.myproject_host_get_all(context)
        hosts = []
        for host in host_list:
            host_dict = {
                'host_name': host.host_name,
                'usage': host.cpu_usage,
                }
            hosts.append(host_dict)

        return {'hosts': hosts}
