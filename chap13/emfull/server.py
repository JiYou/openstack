import hashlib
import struct
import os
from bisect import bisect_left
import random

class Server(object):
    def __init__(self, server_num=5, vnode_num=100):
        self._server_num = server_num
        self._vnode_in_ring = []
        self._vnode_2_server = []
        self._vnode_num = vnode_num
        self._file_record = {}

        for i in range(self._server_num):
            dir_path = '/tmp/server%s' % i
            if not os.path.isdir(dir_path):
                os.mkdir('/tmp/server%s' % i)

        vstep = (1<<32) / self._vnode_num
        step = self._vnode_num / self._server_num
        for i in range(self._vnode_num):
            self._vnode_in_ring.append(vstep*(i+1))
            self._vnode_2_server.append(i%self._server_num)
            self._file_record[i] = []

    def _md5_hash(self, content):
        md5obj = hashlib.md5()
        md5obj.update(content)
        md5_value = md5obj.digest()
        hash_value = struct.unpack_from('>I', md5_value)[0]
        return hash_value % (1<<32)

    def _hash_object(self, file_path):
        with open(file_path, 'rb') as f:
            return self._md5_hash(f.read())

    def _get_server(self, file_path):
        hash_value = self._hash_object(file_path)
        viter = bisect_left(self._vnode_in_ring, hash_value) % \
                len(self._vnode_in_ring)
        self._file_record[viter].append(file_path)
        server_id = self._vnode_2_server[viter]
        return server_id

    def _node_dict(self):
        dc = {}
        for i in range(self._server_num):
            dc[i] = []
            for vnid, nid in enumerate(self._vnode_2_server):
                if nid == i:
                    dc[i].append(vnid)

        return dc

    def add_server(self, add_server_num):
        dc = self._node_dict()
        moved_vnode_num = self._vnode_num / (self._server_num  + add_server_num)
        moved_vnode_from_server = moved_vnode_num / self._server_num
        self._server_num = self._server_num + add_server_num

        vnode_moved_list = []
        if moved_vnode_from_server > 1:
            for i in range(self._server_num):
                choosed_list = random.sample(dc[i], moved_vnode_from_server)
                for x in choosed_list:
                    vnode_moved_list.append(x)
        else:
            vnode_list = []
            for i in range(self._vnode_num):
                vnode_list.append(i)
            vnode_moved_list = random.sample(vnode_list, moved_vnode_num)

        return vnode_moved_list

    def move_files(self, vnode_moved_list, server_id):
        moved_files_cnt = 0
        new_vnode_2_server = self._vnode_2_server
        for i in vnode_moved_list:
            vnode_id = vnode_moved_list[i]
            old_server_id = self._vnode_2_server[vnode_id]
            if old_server_id != server_id:
                for f in self._file_record[vnode_id]]:
                    fn = [i for i in f.split('/')][-1]
                    os.popen('mv /tmp/server$s /tmp/server$s' \
                        % (old_server_id, server_id))
                    moved_files_cnt = moved_files_cnt + 1
            self._vnode_2_server[vnode_id] = server_id

        return moved_files_cnt

    def store(self, file_path):
        if os.path.isfile(file_path):
            ith_server = self._get_server(file_path)
            os.popen('cp -rf %s /tmp/server%s' % (file_path, ith_server))
        else:
            print 'We need to store files!'
