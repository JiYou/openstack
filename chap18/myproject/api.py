from nova.myproject import manager
    
class API(object):
    def __init__(self):
        self.manager = manager.MyProjectManager()

    def get_all_cpu_usage(self, context):
        return self.manager.get_all_cpu_usage(context)
