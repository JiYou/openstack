import hashlib
import struct
import os
import random
import time
from amqplib import client_0_8 as amqp
from bisect import bisect_left

class FileServer(object):
    def __init__(self, server_num=5, vnode_num=100):
        self._server_num = server_num
        self._vnode_in_ring = []
        self._vnode_2_server = []
        self._vnode_num = vnode_num
        self._file_record = {}

        self._create_dir()

        vstep = (1<<32) / self._vnode_num
        step = self._vnode_num / self._server_num
        for i in range(self._vnode_num):
            self._vnode_in_ring.append(vstep*(i+1))
            self._vnode_2_server.append(i%self._server_num)
            self._file_record[i] = []

    def _create_dir(self):
        for i in range(self._server_num):
            dir_path = '/tmp/server%s' % i
            if not os.path.isdir(dir_path):
                os.mkdir('/tmp/server%s' % i)

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
        return server_id, hash_value

    def _node_dict(self):
        dc = {}
        for i in range(self._server_num):
            dc[i] = []
            for vnid, nid in enumerate(self._vnode_2_server):
                if nid == i:
                    dc[i].append(vnid)

        return dc

    def add_server(self, add_server_num=1):
        dc = self._node_dict()
        moved_vnode_num = self._vnode_num / (self._server_num  + add_server_num)
        moved_vnode_from_server = moved_vnode_num / self._server_num

        new_server_list = []
        for i in range(add_server_num):
            new_server_list.append(self._server_num + i)

        self._server_num = self._server_num + add_server_num
        self._create_dir()

        vnode_moved_list = []
        if moved_vnode_from_server > 1:
            for i in range(self._server_num - add_server_num):
                choosed_list = random.sample(dc[i], moved_vnode_from_server)
                for x in choosed_list:
                    vnode_moved_list.append(x)
        else:
            print "Less vnode need to move, randomly choose vnode."
            _re = [len(dc[i]) for i in range(self._server_num - add_server_num)]
            while moved_vnode_num > 0:
                mv = max(_re)
                pos = [i for i in range(len(_re)) if _re[i]==mv][0]
                if 0 == mv:
                    break
                choosed_vnode = random.sample(dc[pos], 1)[0]
                dc[pos].remove(choosed_vnode)
                _re[pos] = _re[pos] - 1
                vnode_moved_list.append(choosed_vnode)
                moved_vnode_num = moved_vnode_num - 1

        if len(vnode_moved_list) == 0:
            return 0

        return self._move_files(vnode_moved_list, new_server_list)

    def _move_files(self, vnode_moved_list, new_server_list):
        moved_files_cnt = 0
        new_vnode_2_server = self._vnode_2_server
        for i in range(len(vnode_moved_list)):
            server_id = random.sample(new_server_list, 1)[0]
            if len(vnode_moved_list) == 0:
                continue
            vnode_id = vnode_moved_list[i]
            old_server_id = self._vnode_2_server[vnode_id]
            if old_server_id != server_id:
                for f in self._file_record[vnode_id]:
                    hash_value = self._hash_object(f)
                    f_path = '/tmp/server%s/%s' % (old_server_id, hash_value)
                    if os.path.isfile(f_path):
                        os.popen('mv %s /tmp/server%s/' % \
                                 (f_path, server_id))
                        moved_files_cnt = moved_files_cnt + 1
                        print "Move %s to /tmp/server%s/" % \
                                 (f_path, server_id)
            new_vnode_2_server[vnode_id] = server_id

        self._vnode_2_server = new_vnode_2_server

        self.vnode_info()

        return moved_files_cnt

    def vnode_info(self):
        dc = self._node_dict()
        for i in range(self._server_num):
            print "Server %s has %s novdes" % (i, len(dc[i]))

    def store(self, file_path):
        if os.path.isfile(file_path):
            ith_server, hash_value = self._get_server(file_path)
            os.popen('cp -rf %s /tmp/server%s/%s' % \
                    (file_path, ith_server, hash_value))
            print "Revieved file %s, store to /tmp/server%s/%s" % \
                    (file_path, ith_server, hash_value)
        else:
            print 'We need to store files!'


_fs = None

def recv_callback(msg):
    global _fs
    global chan
    file_path = msg.body

    if _fs is None:
        _fs = FileServer()

    if msg.body == 'add_server':
        moved_files = _fs.add_server()
        print "Moved files = %s" % moved_files
    elif msg.body == 'vnode_info':
        _fs.vnode_info()
    else:
        _fs.store(file_path)

def main():
    conn = amqp.Connection(host="localhost:5672",
                           userid="guest",
                           password="guest",
                           virtual_host="/",
                           insist=False)
    chan = conn.channel()

    chan.queue_declare(queue="file_storage",
                       durable=True,
                       exclusive=False,
                       auto_delete=False)
    chan.exchange_declare(exchange="cloud_storage",
                       type="direct",
                       durable=True,
                       auto_delete=False,)

    chan.queue_bind(queue="file_storage",
                    exchange="cloud_storage",
                    routing_key="router_key")

    chan.basic_consume(queue='file_storage',
                       no_ack=True,
                       callback=recv_callback)
    while True:
        chan.wait()

    chan.close()
    conn.close()

if __name__ == '__main__':
    main()
