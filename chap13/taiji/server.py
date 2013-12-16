import hashlib
import struct
import os
from bisect import bisect_left

class Server(object):
    def __init__(self, server_num=5):
        self._server_num = server_num
        self._server_in_ring = []
        self._server_dict = {}
        for i in range(self._server_num):
            dir_path = '/tmp/server%s' % i
            if not os.path.isdir(dir_path):
                os.mkdir('/tmp/server%s' % i)

            server_hash = self._md5_server('server%s' % i)
            self._server_in_ring.append(server_hash)
            self._server_dict[server_hash] = i

        self._server_in_ring.sort()

    def _md5_hash(self, content):
        md5obj = hashlib.md5()
        md5obj.update(content)
        md5_value = md5obj.digest()
        hash_value = struct.unpack_from('>I', md5_value)[0]
        return hash_value % (1<<32)

    def _hash_object(self, file_path):
        with open(file_path, 'rb') as f:
            return self._md5_hash(f.read())

    def _md5_server(self, server_ip):
        return self._md5_hash(server_ip)

    def _get_server(self, file_path):
        hash_value = self._hash_object(file_path)
        iter = bisect_left(self._server_in_ring, hash_value) % \
                len(self._server_in_ring)
        server_hash = self._server_in_ring[iter]
        return self._server_dict[server_hash]

    def store(self, file_path):
        if os.path.isfile(file_path):
            ith_server = self._get_server(file_path)
            os.popen('cp -rf %s /tmp/server%s' % (file_path, ith_server))
        else:
            print 'We need to store files!'
