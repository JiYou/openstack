from oslo.config import cfg

myproject_opts = [
    cfg.StrOpt('myproject_topic',
               default='myproject',
               help='the topic myproject nodes listen on'),
    cfg.StrOpt('myproject_manager',
               default='nova.myproject.manager.MyProjectManager',
               help='Manager for myproject'),
           ]

CONF = cfg.CONF
CONF.register_opts(myproject_opts)
