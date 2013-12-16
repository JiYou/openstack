import hashlib
import struct
import os

class Server(object):
    def __init__(self):
        self._server_num = 5
        for i in range(self._server_num):
            dir_path = '/tmp/server%s' % i
            if not os.path.isdir(dir_path):
                os.mkdir('/tmp/server%s' % i)

    def _md5_hash(self, file_path):
        with open(file_path, 'rb') as f:
            md5obj = hashlib.md5()
            md5obj.update(f.read())
            md5_value = md5obj.digest()
            hash_value = struct.unpack_from('>I', md5_value)[0]
            return hash_value

    def _get_server(self, hash_value):
        return hash_value % self._server_num

    def store(self, file_path):
        if os.path.isfile(file_path):
            ith_server = self._get_server(self._md5_hash(file_path))
            os.popen('cp -rf %s /tmp/server%s' % (file_path, ith_server))
        else:
            print 'We need to store files!'
