from novaclient.v1_1 import client as nova_client
from nova.myproject.client import myproject_extension_manager

user_info = {
    'username':'nova',
    'password':'%KEYSTONE_NOVA_PASSWORD%',
    'tenant':'service',
    'authurl':'http://%KEYSTONE_HOST%:5000/v2.0'
}

class ExtensionManagerMeta(object):

    def __init__(self, name, manager_class):
        self.name = name
        self.manager_class = manager_class

extensions=[ExtensionManagerMeta(
                'myproject_extension_manager',
                myproject_extension_manager.MyProjectExtensionManager)]

client = nova_client.Client(user_info.get('username'),
                            user_info.get('password'),
                            project_id=user_info.get('tenant'),
                            auth_url=user_info.get('authurl'),
                            extensions=extensions)
# 19.4.2

print 'Calling cpu_usage...'
print client.myproject_extension_manager.cpu_usage('%HOST_NAME%')

# 19.4.3

print 'Calling cpu_usage2...'
print client.myproject_extension_manager.cpu_usage2('%HOST_NAME%')

# 19.4.4

print 'Calling cpu_usage_all...'
print client.myproject_extension_manager.cpu_usage_all()


