from novaclient.v1_1 import client as nova_client
from nova.myproject.client import simple_extension_manager

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
                'simple_extension_manager',
                simple_extension_manager.SimpleExtensionManager)]

client = nova_client.Client(user_info.get('username'),
                            user_info.get('password'),
                            project_id=user_info.get('tenant'),
                            auth_url=user_info.get('authurl'),
                            extensions=extensions)

print client.simple_extension_manager.is_ok()
