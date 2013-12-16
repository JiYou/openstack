import os
import server
import sys
from amqplib import client_0_8 as amqp
from optparse import OptionParser

def _send_msg(message):
    conn = amqp.Connection(host="localhost:5672",
                           userid="guest", 
                           assword="guest",
                           virtual_host="/",
                           insist=False)
    chan = conn.channel()

    msg = amqp.Message(message)
    msg.properties["delivery_mode"] = 2
    chan.basic_publish(msg,exchange="cloud_storage",routing_key="router_key")

    chan.close()
    conn.close()

_conn = None

def get_connection():
    return server.Server()

def main():
    usage = "usage: %prog file_path"
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("Incorrect number of arguments!")
    else:
        file_path = args[0]
        if file_path[0] == '.' or '/' != file_path[0]:
            now_path = os.getcwd()
            abs_path = now_path + '/' + file_path
        elif file_path[0] == '/':
            abs_path = args[0]

    if os.path.isfile(abs_path):
        _send_msg(abs_path)
    elif args[0] == 'add_server':
        _send_msg(args[0])
    elif args[0] == 'vnode_info':
        _send_msg(args[0])
    else:
        print 'You should input an file path!'

if __name__ == '__main__':
    main()
